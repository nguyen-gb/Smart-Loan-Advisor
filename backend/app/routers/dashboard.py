from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io

from ..database import get_db
from ..schemas.prediction import DashboardStats
from ..services.loan_service import LoanService
from ..ml.trainer import train_from_dataframe
from ..ml.predictor import reload_predictor

from ..dependencies import check_role

router = APIRouter(
    prefix="/dashboard", 
    tags=["Dashboard"],
    dependencies=[Depends(check_role(["manager"]))]
)


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    return LoanService.get_dashboard_stats(db)

@router.post("/ml/train-upload")
async def train_from_file(file: UploadFile = File(...)):
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file CSV (.csv) hoặc Excel (.xlsx, .xls)"
        )

    try:
        contents = await file.read()

        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        print(f"[UPLOAD] Read {len(df)} rows from {file.filename}")
        print(f"[UPLOAD] Columns: {list(df.columns)}")

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Không thể đọc file: {str(e)}"
        )

    result = train_from_dataframe(df)

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Dữ liệu không hợp lệ",
                "errors": result["errors"],
                "warnings": result["warnings"]
            }
        )

    reload_predictor()

    return {
        "message": f"Training từ file '{file.filename}' hoàn tất!",
        "package_accuracy": result["package_accuracy"],
        "risk_accuracy": result["risk_accuracy"],
        "n_samples": result["n_samples"],
        "warnings": result["warnings"]
    }


@router.get("/ml/status")
def ml_model_status():
    import os
    from ..config import PACKAGE_MODEL_PATH, RISK_MODEL_PATH

    pkg_exists = os.path.exists(PACKAGE_MODEL_PATH)
    risk_exists = os.path.exists(RISK_MODEL_PATH)

    return {
        "package_recommender": {
            "loaded": pkg_exists,
            "path": PACKAGE_MODEL_PATH,
        },
        "risk_assessor": {
            "loaded": risk_exists,
            "path": RISK_MODEL_PATH,
        },
        "ready": pkg_exists and risk_exists,
    }
