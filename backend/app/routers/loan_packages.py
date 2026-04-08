from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models.loan_package import LoanPackage
from ..schemas.loan_package import LoanPackageCreate, LoanPackageResponse, LoanPackageUpdate
from ..services.loan_service import LoanService
from ..dependencies import check_role

router = APIRouter(prefix="/packages", tags=["Loan Packages"])


@router.get("/", response_model=List[LoanPackageResponse], dependencies=[Depends(check_role(["staff", "manager"]))])
def list_packages(purpose: Optional[str] = None, db: Session = Depends(get_db)):
    return LoanService.get_packages(db, purpose)


@router.get("/{package_id}", response_model=LoanPackageResponse, dependencies=[Depends(check_role(["staff", "manager"]))])
def get_package(package_id: int, db: Session = Depends(get_db)):
    pkg = LoanService.get_package(db, package_id)
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return pkg


@router.post("/", response_model=LoanPackageResponse, dependencies=[Depends(check_role(["manager"]))])
def create_package(package: LoanPackageCreate, db: Session = Depends(get_db)):
    pkg = LoanPackage(**package.model_dump())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.put("/{package_id}", response_model=LoanPackageResponse, dependencies=[Depends(check_role(["manager"]))])
def update_package(
    package_id: int, package: LoanPackageUpdate, db: Session = Depends(get_db)
):
    pkg = db.query(LoanPackage).filter(LoanPackage.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    update_data = package.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pkg, key, value)

    db.commit()
    db.refresh(pkg)
    return pkg
