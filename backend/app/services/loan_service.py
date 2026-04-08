from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..models.customer import Customer
from ..models.loan_package import LoanPackage
from ..models.loan_application import LoanApplication


class LoanService:

    @staticmethod
    def create_customer(db: Session, **kwargs) -> Customer:
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
