import os
import time
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .etl_service import ETLService
from ..ml.trainer import train_from_dataframe
from ..ml.predictor import reload_predictor
from ..logging_config import get_logger

logger = get_logger("app.services.ml_training")

class MLTrainingService:
    """
    Orchestrates the end-to-end training pipeline:
    DB -> ETL -> Training -> Reload Predictor
    """
    
    _is_training = False
    _last_run_status = None
    _last_run_time = None
    
    @classmethod
    def run_pipeline(cls, db: Session, manual: bool = False):
        if cls._is_training:
            logger.warning("Training is already in progress.")
            return {"status": "in_progress", "message": "Training already running"}
            
        cls._is_training = True
        cls._last_run_status = "training"
        
        start_time = time.time()
        logger.info(f"Starting ML Training Pipeline (Manual: {manual})")
        
        try:
            # 1. ETL - Strictly from DB as requested
            df = ETLService.run_etl_pipeline(db, include_csv=False)
            
            if len(df) < 50:
                msg = f"Dữ liệu không đủ để huấn luyện. Hệ thống tìm thấy {len(df)} hồ sơ hợp lệ (đã được duyệt/thanh toán), cần ít nhất 50 hồ sơ."
                logger.warning(msg)
                cls._last_run_status = "failed"
                return {"status": "error", "message": msg}
            
            # 2. Train
            result = train_from_dataframe(df)
            
            if result["success"]:
                # 3. Reload Models in Running Predictor
                reload_predictor()
                
                duration = time.time() - start_time
                cls._last_run_status = "success"
                cls._last_run_time = datetime.now()
                
                logger.info(f"Training completed successfully in {duration:.2f}s. "
                           f"Package Acc: {result['package_accuracy']:.4f}, Risk Acc: {result['risk_accuracy']:.4f}")
                
                return {
                    "status": "success",
                    "package_accuracy": result["package_accuracy"],
                    "risk_accuracy": result["risk_accuracy"],
                    "n_samples": result["n_samples"],
                    "duration_sec": round(duration, 2)
                }
            else:
                cls._last_run_status = "failed"
                logger.error(f"Training failed: {result.get('errors')}")
                return {"status": "error", "message": "Training script returned failure", "details": result.get("errors")}
                
        except Exception as e:
            cls._last_run_status = "error"
            logger.error(f"Pipeline error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
        finally:
            cls._is_training = False

    @classmethod
    def get_status(cls):
        return {
            "is_training": cls._is_training,
            "last_run_status": cls._last_run_status,
            "last_run_time": cls._last_run_time.isoformat() if cls._last_run_time else None
        }
