from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.customer import CustomerCreate, CustomerResponse
from ..services.loan_service import LoanService
from ..dependencies import check_role

router = APIRouter(
    prefix="/customers", 
    tags=["Customers"],
    dependencies=[Depends(check_role(["manager"]))]
)


@router.post("/", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    return LoanService.create_customer(db, **customer.model_dump())


@router.get("/", response_model=List[CustomerResponse])
def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return LoanService.get_customers(db, skip, limit)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = LoanService.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
