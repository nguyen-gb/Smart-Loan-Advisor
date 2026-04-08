from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=18, le=70)
    gender: str = Field(..., pattern="^(male|female)$")
    marital_status: str = Field(..., pattern="^(single|married|divorced)$")
    monthly_income: float = Field(..., gt=0, description="Thu nhập hàng tháng (triệu VND)")
    living_expenses: float = Field(..., ge=0, description="Chi phí sinh hoạt hàng tháng (triệu VND)")
    current_debt: float = Field(..., ge=0, description="Nợ hiện tại (triệu VND)")
    asset_value: float = Field(..., ge=0, description="Giá trị tài sản (triệu VND)")
    dependents: int = Field(..., ge=0, description="Số người phụ thuộc")
    housing_status: str = Field(..., pattern="^(own|rent|stay_with_parents)$", description="Tình trạng nhà ở")
    collateral_assets: Optional[str] = Field(None, description="Tài sản đảm bảo")
    occupation: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerResponse(CustomerBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
