from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import traceback

from ..database import get_db
from ..logging_config import get_logger
from ..schemas.prediction import (
    PredictionInput, PredictionResponse, PackageRecommendation,
    LoanApplicationCreate
)
from ..models.loan_application import LoanApplication

logger = get_logger("app.routers.predictions")
from ..ml.predictor import get_predictor, reload_predictor
from ..services.loan_service import LoanService
from ..dependencies import check_role

router = APIRouter(prefix="/predictions", tags=["ML Predictions"])

@router.post("/recommend", response_model=PredictionResponse, dependencies=[Depends(check_role(["staff", "manager"]))])
def recommend_packages(input_data: PredictionInput, db: Session = Depends(get_db)):
    try:
        # Lấy lịch sử khách hàng để làm giàu dữ liệu đầu vào cho ML
        history = LoanService.get_customer_loan_history(db, input_data.cccd)
        
        predictor = get_predictor()
        recommendations = predictor.predict(
            age=input_data.age,
            gender=input_data.gender,
            marital_status=input_data.marital_status,
            monthly_income=input_data.monthly_income,
            loan_amount=input_data.loan_amount,
            purpose=input_data.purpose,
            loan_term_months=input_data.loan_term_months,
            living_expenses=input_data.living_expenses,
            current_debt=input_data.current_debt,
            asset_value=input_data.asset_value,
            dependents=input_data.dependents,
            housing_status=input_data.housing_status,
            collateral_assets=input_data.collateral_assets,
            repayment_method=input_data.repayment_method,
            is_returning_customer=history["is_returning"],
            active_loan_count=history["active_loan_count"],
            historical_on_time_rate=history["historical_on_time_rate"],
            top_k=3,
        )

        assessment, advice = predictor.get_overall_assessment(recommendations, input_data.model_dump())

        return PredictionResponse(
            customer_info={
                "cccd": input_data.cccd,
                "age": input_data.age,
                "gender": input_data.gender,
                "marital_status": input_data.marital_status,
                "monthly_income": input_data.monthly_income,
                "loan_amount": input_data.loan_amount,
                "purpose": input_data.purpose,
                "loan_term_months": input_data.loan_term_months,
                "living_expenses": input_data.living_expenses,
                "current_debt": input_data.current_debt,
                "asset_value": input_data.asset_value,
                "dependents": input_data.dependents,
                "housing_status": input_data.housing_status,
                "collateral_assets": input_data.collateral_assets,
            },
            recommendations=[PackageRecommendation(**r) for r in recommendations],
            overall_risk_assessment=assessment,
            advice=advice,
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


@router.post("/apply", dependencies=[Depends(check_role(["staff", "manager"]))])
def create_loan_application(
    app_data: LoanApplicationCreate, db: Session = Depends(get_db)
):
    try:
        customer = LoanService.create_customer(
            db,
            cccd=app_data.cccd,
            name=app_data.customer_name,
            age=app_data.age,
            gender=app_data.gender,
            marital_status=app_data.marital_status,
            monthly_income=app_data.monthly_income,
            living_expenses=app_data.living_expenses,
            current_debt=app_data.current_debt,
            asset_value=app_data.asset_value,
            dependents=app_data.dependents,
            housing_status=app_data.housing_status,
            collateral_assets=app_data.collateral_assets,
        )

        pkg = LoanService.get_package(db, app_data.package_id)
        if not pkg:
            raise HTTPException(status_code=404, detail="Package not found")

        application = LoanService.create_application(
            db,
            customer_id=customer.id,
            cccd=app_data.cccd,
            package_id=app_data.package_id,
            loan_amount=app_data.loan_amount,
            loan_term_months=app_data.loan_term_months,
            payment_period=app_data.payment_period,
            repayment_method=app_data.repayment_method,
            interest_rate=pkg.base_interest_rate,
            purpose=app_data.purpose,
            
            age=app_data.age,
            gender=app_data.gender,
            marital_status=app_data.marital_status,
            monthly_income=app_data.monthly_income,
            living_expenses=app_data.living_expenses,
            current_debt=app_data.current_debt,
            asset_value=app_data.asset_value,
            dependents=app_data.dependents,
            housing_status=app_data.housing_status,
            collateral_assets=app_data.collateral_assets,
            
            risk_score=app_data.risk_score,
            recommended_by_ml=True,
        )

        return {
            "status": "success",
            "id": int(application.id),
            "message": "Hồ sơ đã được tạo thành công"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating loan application for {app_data.customer_name}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.get("/applications", dependencies=[Depends(check_role(["manager"]))])
def list_applications(
    skip: int = 0, limit: int = 50,
    status: str = None, purpose: str = None,
    db: Session = Depends(get_db)
):
    apps = LoanService.get_applications(db, skip, limit, status, purpose)
    total = LoanService.get_applications_count(db, status, purpose)
    
    items = []
    for app in apps:
        items.append({
            "id": app.id,
            "cccd": app.cccd,
            "customer_name": app.customer.name if app.customer else "N/A",
            "package_name": app.package.name if app.package else "N/A",
            "loan_amount": app.loan_amount,
            "loan_term_months": app.loan_term_months,
            "interest_rate": app.interest_rate,
            "purpose": app.purpose,
            "status": app.status,
            "risk_score": app.risk_score,
            "repayment_method": app.repayment_method,
            "is_on_time_payment": app.is_on_time_payment,
            "recommended_by_ml": app.recommended_by_ml,
            "created_at": app.created_at.isoformat() if app.created_at else None,
        })
    
    return {
        "total": total,
        "items": items,
        "page": (skip // limit) + 1,
        "limit": limit
    }


@router.put("/applications/{app_id}/status", dependencies=[Depends(check_role(["manager"]))])
def update_application_status(
    app_id: int, status: str, db: Session = Depends(get_db)
):
    app = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại")
    
    if app.is_on_time_payment is not None:
        raise HTTPException(status_code=400, detail="Hồ sơ đã hoàn tất thanh toán, không thể thay đổi trạng thái duyệt")

    app.status = status
    db.commit()
    return {"message": f"Hồ sơ {app_id} đã chuyển sang trạng thái: {status}"}


@router.put("/applications/{app_id}/payment", dependencies=[Depends(check_role(["manager"]))])
def update_payment_status(
    app_id: int, is_on_time: bool, db: Session = Depends(get_db)
):
    app = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại")
    
    if app.status == "rejected":
        raise HTTPException(status_code=400, detail="Hồ sơ đã bị từ chối, không thể cập nhật thanh toán")
    
    if app.status == "pending":
        raise HTTPException(status_code=400, detail="Hồ sơ chưa được duyệt, không thể cập nhật thanh toán")

    if app.is_on_time_payment is not None:
        raise HTTPException(status_code=400, detail="Hồ sơ đã được cập nhật trạng thái thanh toán trước đó và không thể thay đổi")

    app.is_on_time_payment = is_on_time
    db.commit()
    return {"message": f"Cập nhật trạng thái thanh toán hồ sơ {app_id} thành công"}
