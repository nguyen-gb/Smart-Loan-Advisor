import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from .preprocessor import DataPreprocessor
from ..config import (
    PACKAGE_MODEL_PATH, PACKAGE_ENCODER_PATH, PACKAGE_SCALER_PATH,
    RISK_MODEL_PATH, RISK_SCALER_PATH, FEATURE_COLUMNS_PATH, ML_MODELS_DIR
)

REQUIRED_COLUMNS = [
    "age", "gender", "marital_status", "monthly_income",
    "living_expenses", "current_debt", "asset_value", "dependents", "housing_status",
    "loan_amount", "purpose", "loan_term_months", "repayment_method", "package_id", "is_on_time_payment",
    "is_returning_customer", "active_loan_count", "historical_on_time_rate"
]

VALID_GENDERS = ["male", "female"]
VALID_MARITAL = ["single", "married", "divorced"]
VALID_PURPOSES = ["bds", "o_to", "tieu_dung", "kinh_doanh"]
VALID_HOUSING = ["own", "rent", "stay_with_parents"]


def validate_training_data(df: pd.DataFrame) -> dict:
    errors = []
    warnings = []

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Thiếu các cột: {', '.join(missing_cols)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "clean_df": None}

    clean_df = df[REQUIRED_COLUMNS].copy()

    original_len = len(clean_df)
    clean_df = clean_df.dropna()
    if len(clean_df) < original_len:
        warnings.append(f"Đã bỏ {original_len - len(clean_df)} hàng có dữ liệu trống")

    try:
        clean_df["age"] = clean_df["age"].astype(int)
        clean_df["monthly_income"] = clean_df["monthly_income"].astype(float)
        clean_df["living_expenses"] = clean_df["living_expenses"].astype(float)
        clean_df["current_debt"] = clean_df["current_debt"].astype(float)
        clean_df["asset_value"] = clean_df["asset_value"].astype(float)
        clean_df["dependents"] = clean_df["dependents"].astype(int)
        clean_df["loan_amount"] = clean_df["loan_amount"].astype(float)
        clean_df["loan_term_months"] = clean_df["loan_term_months"].astype(int)
        clean_df["package_id"] = clean_df["package_id"].astype(int)
        clean_df["is_on_time_payment"] = clean_df["is_on_time_payment"].astype(int)
    except (ValueError, TypeError) as e:
        errors.append(f"Lỗi kiểu dữ liệu: {str(e)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "clean_df": None}

    invalid_gender = clean_df[~clean_df["gender"].isin(VALID_GENDERS)]
    if len(invalid_gender) > 0:
        warnings.append(f"Bỏ {len(invalid_gender)} hàng có gender không hợp lệ")
        clean_df = clean_df[clean_df["gender"].isin(VALID_GENDERS)]

    invalid_marital = clean_df[~clean_df["marital_status"].isin(VALID_MARITAL)]
    if len(invalid_marital) > 0:
        warnings.append(f"Bỏ {len(invalid_marital)} hàng có marital_status không hợp lệ")
        clean_df = clean_df[clean_df["marital_status"].isin(VALID_MARITAL)]

    invalid_housing = clean_df[~clean_df["housing_status"].isin(VALID_HOUSING)]
    if len(invalid_housing) > 0:
        warnings.append(f"Bỏ {len(invalid_housing)} hàng có housing_status không hợp lệ")
        clean_df = clean_df[clean_df["housing_status"].isin(VALID_HOUSING)]

    invalid_purpose = clean_df[~clean_df["purpose"].isin(VALID_PURPOSES)]
    if len(invalid_purpose) > 0:
        warnings.append(f"Bỏ {len(invalid_purpose)} hàng có purpose không hợp lệ")
        clean_df = clean_df[clean_df["purpose"].isin(VALID_PURPOSES)]

    if len(clean_df) < 50:
        errors.append(f"Cần ít nhất 50 hàng dữ liệu hợp lệ, chỉ có {len(clean_df)}")
        return {"valid": False, "errors": errors, "warnings": warnings, "clean_df": None}

    n_labels = clean_df["package_id"].nunique()
    if n_labels < 2:
        errors.append(f"Cần ít nhất 2 loại package_id khác nhau, chỉ có {n_labels}")
        return {"valid": False, "errors": errors, "warnings": warnings, "clean_df": None}

    return {"valid": True, "errors": errors, "warnings": warnings, "clean_df": clean_df}


def _run_training_pipeline(df: pd.DataFrame) -> dict:
    os.makedirs(ML_MODELS_DIR, exist_ok=True)

    print(f"\n[1/2] Training Package Recommender (Random Forest)...")

    preprocessor_pkg = DataPreprocessor()
    features = [
        "age", "gender", "marital_status", "monthly_income",
        "living_expenses", "current_debt", "asset_value", "dependents", "housing_status",
        "loan_amount", "purpose", "loan_term_months", "repayment_method",
        "is_returning_customer", "active_loan_count", "historical_on_time_rate"
    ]
    target_pkg = "package_id"

    X = df[features].copy()
    y = df[target_pkg].copy()

    X_processed = preprocessor_pkg.fit_transform(X)
    feature_cols = preprocessor_pkg.get_feature_names()
    X_features = X_processed[feature_cols]

    X_train, X_test, y_train, y_test = train_test_split(
        X_features, y, test_size=0.2, random_state=42, stratify=y
    )

    pkg_model = RandomForestClassifier(
        n_estimators=200, max_depth=15,
        min_samples_split=5, min_samples_leaf=2,
        random_state=42, n_jobs=-1
    )
    pkg_model.fit(X_train, y_train)

    y_pred = pkg_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  [OK] Package Accuracy: {accuracy:.4f}")

    joblib.dump(pkg_model, PACKAGE_MODEL_PATH)
    preprocessor_pkg.save(PACKAGE_ENCODER_PATH, PACKAGE_SCALER_PATH, FEATURE_COLUMNS_PATH)

    print(f"\n[2/2] Training Risk Assessor (Gradient Boosting)...")

    features = [
        "age", "gender", "marital_status", "monthly_income",
        "living_expenses", "current_debt", "asset_value", "dependents", "housing_status",
        "loan_amount", "purpose", "loan_term_months", "repayment_method",
        "is_returning_customer", "active_loan_count", "historical_on_time_rate"
    ]
    target_risk = "is_on_time_payment"

    preprocessor_risk = DataPreprocessor()
    X_risk = df[features].copy()
    y_risk = df[target_risk].copy()

    X_risk_processed = preprocessor_risk.fit_transform(X_risk)
    risk_feature_cols = preprocessor_risk.get_feature_names()
    X_risk_features = X_risk_processed[risk_feature_cols]

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X_risk_features, y_risk, test_size=0.2, random_state=42
    )

    risk_model = GradientBoostingClassifier(
        n_estimators=150, max_depth=5,
        learning_rate=0.1, min_samples_split=5, random_state=42
    )
    risk_model.fit(X_train_r, y_train_r)

    y_pred_r = risk_model.predict(X_test_r)
    accuracy_r = accuracy_score(y_test_r, y_pred_r)
    print(f"  [OK] Risk Accuracy: {accuracy_r:.4f}")

    joblib.dump(risk_model, RISK_MODEL_PATH)
    risk_encoder_path = RISK_MODEL_PATH.replace(".joblib", "_encoder.joblib")
    risk_columns_path = RISK_MODEL_PATH.replace(".joblib", "_columns.joblib")
    preprocessor_risk.save(risk_encoder_path, RISK_SCALER_PATH, risk_columns_path)

    return {
        "package_accuracy": accuracy,
        "risk_accuracy": accuracy_r,
        "n_samples": len(df)
    }


def train_from_dataframe(df: pd.DataFrame) -> dict:
    print("=" * 60)
    print("MODEL TRAINING (Imported data)")
    print("=" * 60)

    validation = validate_training_data(df)
    if not validation["valid"]:
        return {
            "success": False,
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "n_samples": 0
        }

    clean_df = validation["clean_df"]
    print(f"[OK] Validated {len(clean_df)} records")

    result = _run_training_pipeline(clean_df)

    return {
        "success": True,
        "package_accuracy": result["package_accuracy"],
        "risk_accuracy": result["risk_accuracy"],
        "n_samples": result["n_samples"],
        "warnings": validation["warnings"],
        "errors": []
    }


if __name__ == "__main__":
    print("Sử dụng train_from_dataframe để huấn luyện model từ dữ liệu thực tế.")
