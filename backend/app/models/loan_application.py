from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship

from ..database import Base


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    cccd = Column(String(20), index=True, nullable=True)  # Snapshot at time of application
    package_id = Column(Integer, ForeignKey("loan_packages.id"), nullable=False)
    loan_amount = Column(Float, nullable=False)  # triệu VND
    loan_term_months = Column(Integer, nullable=False)
    payment_period = Column(String(20), nullable=False)  # monthly, quarterly
    interest_rate = Column(Float, nullable=False)
    purpose = Column(String(50), nullable=False)
    repayment_method = Column(String(50), nullable=False, default="installment")  # installment, interest_only

    
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    marital_status = Column(String(20), nullable=True)
    monthly_income = Column(Float, nullable=True)
    living_expenses = Column(Float, nullable=True)
    current_debt = Column(Float, nullable=True)
    asset_value = Column(Float, nullable=True)
    dependents = Column(Integer, nullable=True)
    housing_status = Column(String(50), nullable=True)
    collateral_assets = Column(String(200), nullable=True)

    status = Column(String(20), default="pending")  # pending, approved, rejected
    is_on_time_payment = Column(Boolean, nullable=True)  # null = chưa biết
    risk_score = Column(Float, nullable=True)  # 0~1, ML dự báo
    recommended_by_ml = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    customer = relationship("Customer", backref="applications")
    package = relationship("LoanPackage", backref="applications")
