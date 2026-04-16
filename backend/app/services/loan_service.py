from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..models.customer import Customer
from ..models.loan_package import LoanPackage
from ..models.loan_application import LoanApplication


class LoanService:

    @staticmethod
    def create_customer(db: Session, **kwargs) -> Customer:
        cccd = kwargs.get("cccd")
        if cccd:
            existing = db.query(Customer).filter(Customer.cccd == cccd).first()
            if existing:
                # Cập nhật thông tin mới nhất
                for key, value in kwargs.items():
                    setattr(existing, key, value)
                db.commit()
                db.refresh(existing)
                return existing
        
        customer = Customer(**kwargs)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        return db.query(Customer).offset(skip).limit(limit).all()

    @staticmethod
    def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def get_packages(db: Session, purpose: Optional[str] = None) -> List[LoanPackage]:
        query = db.query(LoanPackage)
        if purpose:
            query = query.filter(LoanPackage.purpose == purpose)
        return query.filter(LoanPackage.is_active == 1).all()

    @staticmethod
    def get_package(db: Session, package_id: int) -> Optional[LoanPackage]:
        return db.query(LoanPackage).filter(LoanPackage.id == package_id).first()

    @staticmethod
    def create_application(db: Session, **kwargs) -> LoanApplication:
        app = LoanApplication(**kwargs)
        db.add(app)
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def get_applications(
        db: Session, skip: int = 0, limit: int = 100,
        status: Optional[str] = None, purpose: Optional[str] = None
    ) -> List[LoanApplication]:
        query = db.query(LoanApplication)
        if status:
            query = query.filter(LoanApplication.status == status)
        if purpose:
            query = query.filter(LoanApplication.purpose == purpose)
        return query.order_by(LoanApplication.id.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_applications_count(
        db: Session, status: Optional[str] = None, purpose: Optional[str] = None
    ) -> int:
        query = db.query(func.count(LoanApplication.id))
        if status:
            query = query.filter(LoanApplication.status == status)
        if purpose:
            query = query.filter(LoanApplication.purpose == purpose)
        return query.scalar() or 0

    @staticmethod
    def update_application_status(
        db: Session, app_id: int, status: str
    ) -> Optional[LoanApplication]:
        app = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
        if app:
            app.status = status
            db.commit()
            db.refresh(app)
        return app

    @staticmethod
    def update_payment_status(
        db: Session, app_id: int, is_on_time: bool
    ) -> Optional[LoanApplication]:
        app = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
        if app:
            app.is_on_time_payment = is_on_time
            db.commit()
            db.refresh(app)
        return app

    @staticmethod
    def get_customer_loan_history(db: Session, cccd: str) -> dict:
        apps = db.query(LoanApplication).filter(LoanApplication.cccd == cccd).all()
        active_loans = [a for a in apps if a.status == "approved" and a.is_on_time_payment is None]
        completed_loans = [a for a in apps if a.is_on_time_payment is not None]
        
        on_time_count = sum(1 for a in completed_loans if a.is_on_time_payment)
        on_time_rate = on_time_count / len(completed_loans) if completed_loans else 1.0
        
        return {
            "is_returning": len(apps) > 0,
            "active_loan_count": len(active_loans),
            "historical_on_time_rate": on_time_rate,
            "total_previous_loans": len(apps)
        }

    @staticmethod
    def get_training_data_from_db(db: Session) -> List[dict]:
        apps = db.query(LoanApplication).all()
        data = []
        for app in apps:
            # Lấy lịch sử tại thời điểm đó (đơn giản hóa bằng cách lấy history của CCCD trừ đi chính app này)
            history = db.query(LoanApplication).filter(
                LoanApplication.cccd == app.cccd,
                LoanApplication.id < app.id
            ).all()
            
            prev_completed = [a for a in history if a.is_on_time_payment is not None]
            prev_on_time = sum(1 for a in prev_completed if a.is_on_time_payment)
            
            data.append({
                "age": app.age,
                "gender": app.gender,
                "marital_status": app.marital_status,
                "monthly_income": app.monthly_income,
                "living_expenses": app.living_expenses,
                "current_debt": app.current_debt,
                "asset_value": app.asset_value,
                "dependents": app.dependents,
                "housing_status": app.housing_status,
                "loan_amount": app.loan_amount,
                "purpose": app.purpose,
                "loan_term_months": app.loan_term_months,
                "repayment_method": app.repayment_method,
                "package_id": app.package_id,
                "is_on_time_payment": app.is_on_time_payment,
                "is_returning_customer": 1 if len(history) > 0 else 0,
                "active_loan_count": sum(1 for a in history if a.is_on_time_payment is None and a.status == "approved"),
                "historical_on_time_rate": prev_on_time / len(prev_completed) if prev_completed else 1.0
            })
        return data

    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        total = db.query(func.count(LoanApplication.id)).scalar() or 0
        approved = db.query(func.count(LoanApplication.id)).filter(
            LoanApplication.status == "approved"
        ).scalar() or 0
        rejected = db.query(func.count(LoanApplication.id)).filter(
            LoanApplication.status == "rejected"
        ).scalar() or 0
        pending = db.query(func.count(LoanApplication.id)).filter(
            LoanApplication.status == "pending"
        ).scalar() or 0

        avg_risk = db.query(func.avg(LoanApplication.risk_score)).scalar()

        total_with_payment = db.query(func.count(LoanApplication.id)).filter(
            LoanApplication.is_on_time_payment.isnot(None)
        ).scalar() or 0
        on_time = db.query(func.count(LoanApplication.id)).filter(
            LoanApplication.is_on_time_payment == True
        ).scalar() or 0
        on_time_rate = (on_time / total_with_payment * 100) if total_with_payment > 0 else None

        total_amount = db.query(func.sum(LoanApplication.loan_amount)).scalar() or 0

        purpose_stats = {}
        purpose_rows = db.query(
            LoanApplication.purpose, func.count(LoanApplication.id)
        ).group_by(LoanApplication.purpose).all()
        for purpose, count in purpose_rows:
            purpose_stats[purpose] = count

        pkg_stats = {}
        pkg_rows = db.query(
            LoanPackage.name, func.count(LoanApplication.id)
        ).join(LoanPackage).group_by(LoanPackage.name).all()
        for name, count in pkg_rows:
            pkg_stats[name] = count

        risk_dist = {"low": 0, "medium": 0, "high": 0}
        apps = db.query(LoanApplication.risk_score).filter(
            LoanApplication.risk_score.isnot(None)
        ).all()
        for (score,) in apps:
            if score < 0.3:
                risk_dist["low"] += 1
            elif score < 0.6:
                risk_dist["medium"] += 1
            else:
                risk_dist["high"] += 1

        return {
            "total_applications": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "pending_count": pending,
            "average_risk_score": round(avg_risk, 3) if avg_risk else None,
            "on_time_payment_rate": round(on_time_rate, 1) if on_time_rate else None,
            "total_loan_amount": total_amount,
            "applications_by_purpose": purpose_stats,
            "applications_by_package": pkg_stats,
            "risk_distribution": risk_dist,
        }
