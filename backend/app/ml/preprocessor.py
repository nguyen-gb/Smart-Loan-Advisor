import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Dict
import joblib


class DataPreprocessor:

    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.categorical_columns = ["gender", "marital_status", "purpose", "housing_status", "repayment_method"]
        self.numerical_columns = [
            "age", "monthly_income", "loan_amount", "loan_term_months",
            "living_expenses", "current_debt", "asset_value", "dependents"
        ]

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_processed = df.copy()

        for col in self.categorical_columns:
            if col in df_processed.columns:
                le = LabelEncoder()
                df_processed[col] = le.fit_transform(df_processed[col])
                self.label_encoders[col] = le

        df_processed = self._add_features(df_processed)

        all_numeric = self.numerical_columns + self._get_engineered_feature_names()
        self.feature_columns = self.categorical_columns + all_numeric
        self.scaler.fit(df_processed[all_numeric])
        df_processed[all_numeric] = self.scaler.transform(df_processed[all_numeric])

        return df_processed

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_processed = df.copy()

        for col in self.categorical_columns:
            if col in df_processed.columns and col in self.label_encoders:
                le = self.label_encoders[col]
                known_labels = set(le.classes_)
                df_processed[col] = df_processed[col].map(
                    lambda x: x if x in known_labels else le.classes_[0]
                )
                df_processed[col] = le.transform(df_processed[col])

        df_processed = self._add_features(df_processed)

        all_numeric = self.numerical_columns + self._get_engineered_feature_names()
        df_processed[all_numeric] = self.scaler.transform(df_processed[all_numeric])

        return df_processed

    def _add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["dti_ratio"] = df["loan_amount"] / (df["monthly_income"] * df["loan_term_months"] + 1)
        df["loan_income_ratio"] = df["loan_amount"] / (df["monthly_income"] + 1)
        
        df["total_debt_ratio"] = (df["current_debt"] + df["loan_amount"]) / (df["monthly_income"] * df["loan_term_months"] + 1)
        
        df["net_monthly_income"] = df["monthly_income"] - df["living_expenses"]
        
        df["expense_ratio"] = df["living_expenses"] / (df["monthly_income"] + 1)
        
        df["asset_loan_ratio"] = df["asset_value"] / (df["loan_amount"] + 1)

        df["age_group"] = pd.cut(
            df["age"],
            bins=[0, 25, 35, 45, 55, 100],
            labels=[0, 1, 2, 3, 4]
        ).astype(int)

        df["income_level"] = pd.cut(
            df["monthly_income"],
            bins=[0, 10, 20, 40, 80, 1000],
            labels=[0, 1, 2, 3, 4]
        ).astype(int)

        return df

    def _get_engineered_feature_names(self) -> list:
        return [
            "dti_ratio", "loan_income_ratio", "age_group", "income_level",
            "total_debt_ratio", "net_monthly_income", "expense_ratio", "asset_loan_ratio"
        ]

    def get_feature_names(self) -> list:
        return self.feature_columns + self._get_engineered_feature_names()

    def save(self, encoder_path: str, scaler_path: str, columns_path: str):
        joblib.dump(self.label_encoders, encoder_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump({
            "feature_columns": self.feature_columns,
            "categorical_columns": self.categorical_columns,
            "numerical_columns": self.numerical_columns,
        }, columns_path)

    def load(self, encoder_path: str, scaler_path: str, columns_path: str):
        self.label_encoders = joblib.load(encoder_path)
        self.scaler = joblib.load(scaler_path)
        meta = joblib.load(columns_path)
        self.feature_columns = meta["feature_columns"]
        self.categorical_columns = meta["categorical_columns"]
        self.numerical_columns = meta["numerical_columns"]
