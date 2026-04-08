import os

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_loan.db")

# ML Model paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")

# Package recommendation model
PACKAGE_MODEL_PATH = os.path.join(ML_MODELS_DIR, "package_recommender.joblib")
PACKAGE_ENCODER_PATH = os.path.join(ML_MODELS_DIR, "package_encoder.joblib")
PACKAGE_SCALER_PATH = os.path.join(ML_MODELS_DIR, "package_scaler.joblib")

# Risk assessment model
RISK_MODEL_PATH = os.path.join(ML_MODELS_DIR, "risk_assessor.joblib")
RISK_SCALER_PATH = os.path.join(ML_MODELS_DIR, "risk_scaler.joblib")

# Feature columns
FEATURE_COLUMNS_PATH = os.path.join(ML_MODELS_DIR, "feature_columns.joblib")

# API
API_PREFIX = "/api/v1"
PROJECT_NAME = "Smart Loan Advisor"
PROJECT_VERSION = "1.0.0"

# Auth
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-smart-loan-advisor-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours
