import pandas as pd
import numpy as np
import os
from sqlalchemy.orm import Session
from .loan_service import LoanService
from ..ml.trainer import REQUIRED_COLUMNS

class ETLService:
    """
    Service responsible for Extracting data from DB, 
    Transforming it (cleaning, feature engineering), 
    and preparing it for ML Training.
    """
    
    @staticmethod
    def run_etl_pipeline(db: Session, include_csv: bool = False) -> pd.DataFrame:
        # Extract exclusively from DB
        db_data = LoanService.get_training_data_from_db(db)
        df = pd.DataFrame(db_data)
        
        # Transform - Cleaning
        df = ETLService.clean_data(df)
        
        return df

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
            
        # Remove extreme outliers in age
        df = df[(df["age"] >= 18) & (df["age"] <= 80)]
        
        # Remove records with negative income/amount
        df = df[df["monthly_income"] > 0]
        df = df[df["loan_amount"] > 0]
        
        # Handle missing values
        # For numerical columns, use median
        num_cols = df.select_dtypes(include=[np.number]).columns
        df[num_cols] = df[num_cols].fillna(df[num_cols].median())
        
        # For categorical columns, use mode
        cat_cols = df.select_dtypes(include=[object]).columns
        for col in cat_cols:
            df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "unknown")
            
        # Cap values to prevent skewed models
        if "active_loan_count" in df.columns:
            df["active_loan_count"] = df["active_loan_count"].clip(0, 5)
        
        if "historical_on_time_rate" in df.columns:
            df["historical_on_time_rate"] = df["historical_on_time_rate"].clip(0, 1)
            
        return df
