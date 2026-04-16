from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .ml_training_service import MLTrainingService
from ..logging_config import get_logger

logger = get_logger("app.services.scheduler")

class SchedulerService:
    _scheduler = None

    @classmethod
    def start(cls):
        if cls._scheduler and cls._scheduler.running:
            return
            
        cls._scheduler = BackgroundScheduler()
        
        # Schedule daily training at 2:00 AM
        cls._scheduler.add_job(
            id="daily_model_training",
            func=cls._run_daily_training,
            trigger=CronTrigger(hour=2, minute=0),
            replace_existing=True
        )
        
        cls._scheduler.start()
        logger.info("Scheduler started. Daily model training scheduled for 02:00 AM.")

    @classmethod
    def stop(cls):
        if cls._scheduler:
            cls._scheduler.shutdown()
            logger.info("Scheduler stopped.")

    @staticmethod
    def _run_daily_training():
        logger.info("Executing scheduled daily model training...")
        db = SessionLocal()
        try:
            MLTrainingService.run_pipeline(db, manual=False)
        except Exception as e:
            logger.error(f"Scheduled training failed: {str(e)}")
        finally:
            db.close()
