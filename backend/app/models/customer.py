from sqlalchemy import Column, Integer, String, Float, DateTime, func

from ..database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)  # male, female
    marital_status = Column(String(20), nullable=False)  # single, married, divorced
    monthly_income = Column(Float, nullable=False)  # triệu VND
    living_expenses = Column(Float, nullable=False, default=0.0)  # triệu VND
    current_debt = Column(Float, nullable=False, default=0.0)  # triệu VND
    asset_value = Column(Float, nullable=False, default=0.0)  # triệu VND
    dependents = Column(Integer, nullable=False, default=0)
    housing_status = Column(String(50), nullable=False, default="own")  # own, rent, stay_with_parents
    collateral_assets = Column(String(200), nullable=True)
    occupation = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
