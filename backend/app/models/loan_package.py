from sqlalchemy import Column, Integer, String, Float, Text

from ..database import Base


class LoanPackage(Base):
    __tablename__ = "loan_packages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    purpose = Column(String(50), nullable=False)  # bds, tieu_dung, o_to, kinh_doanh
    min_amount = Column(Float, nullable=False)  # triệu VND
    max_amount = Column(Float, nullable=False)
    base_interest_rate = Column(Float, nullable=False)  # % năm
    floating_rate = Column(Float, nullable=False)  # % năm (thả nổi sau ưu đãi)
    min_term_months = Column(Integer, nullable=False)
    max_term_months = Column(Integer, nullable=False)
    promotion_months = Column(Integer, nullable=False, default=0)  # số tháng ưu đãi
    promotion_rate = Column(Float, nullable=False, default=0)  # lãi suất ưu đãi %
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
