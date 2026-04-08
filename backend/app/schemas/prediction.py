from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PredictionInput(BaseModel):
    age: int = Field(..., ge=18, le=70, description="Tuổi khách hàng")
    gender: str = Field(..., pattern="^(male|female)$", description="Giới tính")
    marital_status: str = Field(
        ..., pattern="^(single|married|divorced)$", description="Tình trạng hôn nhân"
    )
    monthly_income: float = Field(..., gt=0, description="Thu nhập hàng tháng (triệu VND)")
    living_expenses: float = Field(0, ge=0, description="Chi phí sinh hoạt hàng tháng (triệu VND)")
    current_debt: float = Field(0, ge=0, description="Nợ hiện tại (triệu VND)")
    asset_value: float = Field(0, ge=0, description="Giá trị tài sản (triệu VND)")
    dependents: int = Field(0, ge=0, description="Số người phụ thuộc")
    housing_status: str = Field(
        "own", pattern="^(own|rent|stay_with_parents)$", description="Tình trạng nhà ở"
    )
    collateral_assets: Optional[str] = Field(None, description="Tài sản đảm bảo")
    loan_amount: float = Field(..., gt=0, description="Số tiền muốn vay (triệu VND)")
    purpose: str = Field(
        ...,
        description="Mục đích vay: bds, tieu_dung, o_to, kinh_doanh"
    )
    loan_term_months: int = Field(..., gt=0, description="Thời hạn vay mong muốn (tháng)")
    repayment_method: str = Field(
        "installment",
        pattern="^(installment|interest_only)$",
        description="Trả góp (gốc + lãi) | Trả lãi, gốc cuối kì"
    )


class PackageRecommendation(BaseModel):
    package_id: int
    package_name: str
    purpose: str
    confidence: float = Field(..., description="Độ tin cậy (%)")
    base_interest_rate: float
    floating_rate: float
    promotion_months: int
    promotion_rate: float
    min_term_months: int
    max_term_months: int
    risk_score: float = Field(..., description="Điểm rủi ro (0-1, thấp = tốt)")
    risk_level: str = Field(..., description="Mức rủi ro: low, medium, high")
    monthly_payment_estimate: float = Field(..., description="Tổng trả hàng tháng ước tính (triệu VND)")
    monthly_principal_estimate: float = Field(..., description="Gốc trả hàng tháng ước tính (triệu VND)")
    monthly_interest_estimate: float = Field(..., description="Lãi trả hàng tháng ước tính (triệu VND)")
    dti: float = Field(..., description="Tỉ lệ nợ/thu nhập ròng (%)")
    repayment_method: str = Field(..., description="repayment method used for estimate")
    reason: str = Field(..., description="Lý do đề xuất")


class PredictionResponse(BaseModel):
    customer_info: dict
    recommendations: List[PackageRecommendation]
    overall_risk_assessment: str
    advice: str


class LoanApplicationCreate(BaseModel):
    customer_name: str
    age: int
    gender: str
    marital_status: str
    monthly_income: float
    living_expenses: float = 0
    current_debt: float = 0
    asset_value: float = 0
    dependents: int = 0
    housing_status: str = "own"
    collateral_assets: Optional[str] = None
    package_id: int
    loan_amount: float
    loan_term_months: int
    payment_period: str = "monthly"
    repayment_method: str = "installment"
    purpose: str
    risk_score: Optional[float] = None




class DashboardStats(BaseModel):
    total_applications: int
    approved_count: int
    rejected_count: int
    pending_count: int
    average_risk_score: Optional[float]
    on_time_payment_rate: Optional[float]
    total_loan_amount: float
    applications_by_purpose: dict
    applications_by_package: dict
    risk_distribution: dict
