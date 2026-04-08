from pydantic import BaseModel, Field
from typing import Optional


class LoanPackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    purpose: str = Field(..., description="bds, tieu_dung, o_to, kinh_doanh")
    min_amount: float = Field(..., gt=0)
    max_amount: float = Field(..., gt=0)
    base_interest_rate: float = Field(..., gt=0)
    floating_rate: float = Field(..., gt=0)
    min_term_months: int = Field(..., gt=0)
    max_term_months: int = Field(..., gt=0)
    promotion_months: int = Field(0, ge=0)
    promotion_rate: float = Field(0, ge=0)
    description: Optional[str] = None


class LoanPackageCreate(LoanPackageBase):
    pass


class LoanPackageUpdate(BaseModel):
    name: Optional[str] = None
    purpose: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    base_interest_rate: Optional[float] = None
    floating_rate: Optional[float] = None
    min_term_months: Optional[int] = None
    max_term_months: Optional[int] = None
    promotion_months: Optional[int] = None
    promotion_rate: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[int] = None


class LoanPackageResponse(LoanPackageBase):
    id: int
    is_active: int

    class Config:
        from_attributes = True
