from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ml_training_service import MLTrainingService
from ..dependencies import check_role

router = APIRouter(prefix="/ml", tags=["ML Management"])

@router.post("/sync", dependencies=[Depends(check_role(["manager"]))])
async def sync_and_train(db: Session = Depends(get_db)):
    """
    Manually trigger the ETL and Training pipeline.
    """
    status = MLTrainingService.get_status()
    if status["is_training"]:
        return {"status": "in_progress", "message": "Training already running"}
    
    # We run it in the background if possible, or just wait for it.
    # For now, let's wait for it to return a clear result to the user.
    result = MLTrainingService.run_pipeline(db, manual=True)
    return result

@router.get("/status", dependencies=[Depends(check_role(["staff", "manager"]))])
async def get_training_status():
    """
    Check the status of the ML pipeline.
    """
    return MLTrainingService.get_status()
