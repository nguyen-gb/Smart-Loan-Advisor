import os
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Optional

from .preprocessor import DataPreprocessor
from .data_generator import LOAN_PACKAGES
from ..config import (
    PACKAGE_MODEL_PATH, PACKAGE_ENCODER_PATH, PACKAGE_SCALER_PATH,
    RISK_MODEL_PATH, RISK_SCALER_PATH, FEATURE_COLUMNS_PATH
)


class LoanPredictor:

    def __init__(self):
        self.pkg_model = None
        self.risk_model = None
        self.pkg_preprocessor = DataPreprocessor()
        self.risk_preprocessor = DataPreprocessor()
        self._loaded = False

    def load_models(self):
        if not os.path.exists(PACKAGE_MODEL_PATH):
            raise FileNotFoundError(
                "Models not found. Please run training first: upload data at /dashboard/ml/train-upload"
            )

        self.pkg_model = joblib.load(PACKAGE_MODEL_PATH)
        self.pkg_preprocessor.load(
            PACKAGE_ENCODER_PATH, PACKAGE_SCALER_PATH, FEATURE_COLUMNS_PATH
        )

        self.risk_model = joblib.load(RISK_MODEL_PATH)
        risk_encoder_path = RISK_MODEL_PATH.replace(".joblib", "_encoder.joblib")
        risk_columns_path = RISK_MODEL_PATH.replace(".joblib", "_columns.joblib")
        self.risk_preprocessor.load(
            risk_encoder_path, RISK_SCALER_PATH, risk_columns_path
        )

        self._loaded = True

    def predict(
        self,
        age: int,
        gender: str,
        marital_status: str,
        monthly_income: float,
        loan_amount: float,
        purpose: str,
        loan_term_months: int,
        living_expenses: float = 0,
        current_debt: float = 0,
        asset_value: float = 0,
        dependents: int = 0,
        housing_status: str = "own",
        collateral_assets: Optional[str] = None,
        repayment_method: str = "installment",
        is_returning_customer: int = 0,
        active_loan_count: int = 0,
        historical_on_time_rate: float = 1.0,
        top_k: int = 3,
    ) -> List[Dict]:
        if not self._loaded:
            self.load_models()

        input_data = pd.DataFrame([{
            "age": age,
            "gender": gender,
            "marital_status": marital_status,
            "monthly_income": monthly_income,
            "living_expenses": living_expenses,
            "current_debt": current_debt,
            "asset_value": asset_value,
            "dependents": dependents,
            "housing_status": housing_status,
            "loan_amount": loan_amount,
            "purpose": purpose,
            "loan_term_months": loan_term_months,
            "repayment_method": repayment_method,
            "is_returning_customer": is_returning_customer,
            "active_loan_count": active_loan_count,
            "historical_on_time_rate": historical_on_time_rate,
        }])

        X_pkg = self.pkg_preprocessor.transform(input_data.copy())
        feature_cols = self.pkg_preprocessor.get_feature_names()
        X_features = X_pkg[feature_cols]

        pkg_proba = self.pkg_model.predict_proba(X_features)[0]
        pkg_classes = self.pkg_model.classes_

        sorted_indices = np.argsort(pkg_proba)[::-1]

        purpose_pkg_ids = {p["id"] for p in LOAN_PACKAGES if p["purpose"] == purpose}

        recommendations = []
        count = 0
        for idx in sorted_indices:
            if count >= top_k:
                break

            pkg_id = pkg_classes[idx]
            confidence = pkg_proba[idx] * 100

            if pkg_id not in purpose_pkg_ids and confidence < 10:
                continue

            pkg_info = next((p for p in LOAN_PACKAGES if p["id"] == pkg_id), None)
            if not pkg_info:
                continue

            X_risk = self.risk_preprocessor.transform(input_data.copy())
            risk_feature_cols = self.risk_preprocessor.get_feature_names()
            X_risk_features = X_risk[risk_feature_cols]

            risk_proba = self.risk_model.predict_proba(X_risk_features)[0]
            risk_score = float(risk_proba[0])

            # Initial risk level from ML model
            # (We will reassess this after DTI calculation)

            monthly_rate = pkg_info["base_interest_rate"] / 100 / 12
            if repayment_method == "interest_only":
                # Only pay interest monthly, principal at the end
                monthly_interest = loan_amount * monthly_rate
                monthly_principal = 0
                monthly_payment = monthly_interest
            else:
                # Standard installment (principal + interest amortized)
                if monthly_rate > 0 and loan_term_months > 0:
                    monthly_payment = loan_amount * monthly_rate * \
                        (1 + monthly_rate) ** loan_term_months / \
                        ((1 + monthly_rate) ** loan_term_months - 1)
                    monthly_interest = loan_amount * monthly_rate
                    monthly_principal = monthly_payment - monthly_interest
                else:
                    monthly_payment = loan_amount / max(loan_term_months, 1)
                    monthly_interest = 0
                    monthly_principal = monthly_payment
                
            # DTI calculation (Debt-to-Income)
            net_income = monthly_income - living_expenses
            dti_val = (monthly_payment / max(net_income, 0.1)) * 100

            # Rule-based risk override (Guardrails)
            if dti_val > 100:
                risk_score = max(risk_score, 0.85)
            elif dti_val > 80:
                risk_score = max(risk_score, 0.75)
            elif dti_val > 60:
                risk_score = max(risk_score, 0.55)
            elif dti_val > 40:
                risk_score = max(risk_score, 0.40)
            
            # Repayment method risk adjustment
            if repayment_method == "interest_only":
                # Trả lãi cuối kỳ rủi ro cao hơn vì nợ gốc không giảm dần
                risk_score += 0.12 
                if loan_term_months > 60:
                    risk_score += 0.08 # Cực kỳ rủi ro nếu nợ gốc treo quá lâu
            
            risk_score = min(risk_score, 0.99) # Giới hạn tối đa

            # Re-determine final risk level
            if risk_score < 0.3:
                risk_level = "low"
            elif risk_score < 0.6:
                risk_level = "medium"
            else:
                risk_level = "high"

            reason = self._generate_reason(
                pkg_info, monthly_income, loan_amount,
                loan_term_months, risk_level, age, marital_status,
                living_expenses, current_debt, repayment_method, dti_val
            )

            recommendations.append({
                "package_id": int(pkg_id),
                "package_name": pkg_info["name"],
                "purpose": pkg_info["purpose"],
                "confidence": round(confidence, 1),
                "base_interest_rate": pkg_info["base_interest_rate"],
                "floating_rate": pkg_info["floating_rate"],
                "promotion_months": pkg_info["promotion_months"],
                "promotion_rate": pkg_info["promotion_rate"],
                "min_term_months": pkg_info["min_term_months"],
                "max_term_months": pkg_info["max_term_months"],
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "monthly_payment_estimate": round(monthly_payment, 3),
                "monthly_principal_estimate": round(monthly_principal, 3),
                "monthly_interest_estimate": round(monthly_interest, 3),
                "dti": round(dti_val, 1),
                "repayment_method": repayment_method,
                "reason": reason,
            })

            count += 1

        return recommendations

    def _generate_reason(
        self, pkg: Dict, income: float, amount: float,
        term: int, risk_level: str, age: int, marital_status: str,
        living_expenses: float = 0, current_debt: float = 0,
        repayment_method: str = "installment", dti: float = 0
    ) -> str:
        reasons = []

        if pkg["promotion_months"] > 0:
            reasons.append(
                f"Ưu đãi lãi suất {pkg['promotion_rate']}% trong {pkg['promotion_months']} tháng đầu"
            )

        monthly_rate = pkg["base_interest_rate"] / 100 / 12
        if monthly_rate > 0 and term > 0:
            if repayment_method == "interest_only":
                monthly_payment = amount * monthly_rate
                reasons.append("⚠️ Rủi ro tăng do nợ gốc không giảm dần hàng tháng")
                reasons.append(f"Phương thức trả lãi hàng tháng: gốc thanh toán cuối kì")
            else:
                monthly_payment = amount * monthly_rate * (1 + monthly_rate) ** term / \
                                  ((1 + monthly_rate) ** term - 1)
                reasons.append(f"Phương thức trả góp: gốc + lãi được chia đều hàng tháng")
            
            if dti < 30:
                reasons.append("Chỉ số DTI rất an toàn so với thu nhập ròng")
            elif dti < 50:
                reasons.append("Chỉ số DTI ở mức hợp lý")
            else:
                reasons.append("⚠️ Chỉ số DTI chiếm tỉ trọng lớn trong thu nhập ròng")

        if current_debt > (income * 12):
            reasons.append("⚠️ Tổng nợ hiện tại khá cao so với thu nhập năm")

        if risk_level == "low":
            reasons.append("Rủi ro thấp - hồ sơ tốt")
        elif risk_level == "medium":
            reasons.append("Rủi ro trung bình - cần xem xét kỹ")
        else:
            reasons.append("⚠️ Rủi ro cao - cân nhắc giảm số tiền vay hoặc tăng thời hạn")

        if term >= 120:
            reasons.append("Thời hạn dài giúp giảm áp lực trả nợ hàng tháng")
        elif term <= 36:
            reasons.append("Thời hạn ngắn giúp tiết kiệm lãi suất tổng")

        return ". ".join(reasons)

    def get_overall_assessment(self, recommendations: List[Dict], input_data: Dict) -> tuple:
        if not recommendations:
            return "Không có đủ dữ liệu để đánh giá", "Vui lòng kiểm tra lại thông tin"

        avg_risk = np.mean([r["risk_score"] for r in recommendations])
        avg_dti = np.mean([r["dti"] for r in recommendations])
        
        income = input_data.get("monthly_income", 0)
        living_expenses = input_data.get("living_expenses", 0)
        net_income = max(income - living_expenses, 0.1)
        loan_amount = input_data.get("loan_amount", 0)
        loan_term = input_data.get("loan_term_months", 0)
        repayment_method = input_data.get("repayment_method", "installment")
        
        target_dti = 35  # Ngưỡng an toàn thường thấy (35%)
        target_monthly = net_income * (target_dti / 100)
        
        # Lấy lãi suất trung bình từ các khuyến nghị để tính toán gợi ý
        avg_rate = np.mean([r["base_interest_rate"] for r in recommendations]) / 100 / 12

        advice_list = []

        if avg_risk < 0.3:
            assessment = "Hồ sơ tốt - Khả năng được duyệt cao ✅"
            advice_list.append("Khách hàng có hồ sơ tài chính rất tốt")
            advice_list.append("Nên tư vấn các gói có lãi suất ưu đãi dài hạn để tối ưu chi phí")
        elif avg_risk < 0.6:
            assessment = "Hồ sơ trung bình - Cần xem xét thêm ⚠️"
            advice_list.append("Hồ sơ cần củng cố thêm một số yếu tố để tăng tỉ lệ duyệt")
        else:
            assessment = "Hồ sơ rủi ro cao - Cần điều chỉnh phương án 🔴"
            advice_list.append("Khả năng được duyệt hiện tại thấp do các chỉ số tài chính chưa tối ưu")

        # Phân tích các yếu tố gây rủi ro cụ thể
        risk_reasons = []
        if avg_dti > 50:
            risk_reasons.append(f"Tỉ lệ nợ/thu nhập ròng ({avg_dti:.1f}%) vượt ngưỡng báo động")
        if input_data.get("current_debt", 0) > (income * 12):
            risk_reasons.append("Tổng nợ hiện tại đang ở mức cao so với thu nhập năm")
        if input_data.get("asset_value", 0) < loan_amount:
            risk_reasons.append("Giá trị tài sản sở hữu thấp so với quy mô khoản vay")
        if (income - living_expenses) <= 5: # Thu nhập ròng quá thấp (dưới 5tr)
            risk_reasons.append("Thu nhập thặng dư sau chi phí sinh hoạt quá mỏng")
        if input_data.get("age", 0) > 65:
            risk_reasons.append("Khách hàng ở độ tuổi cao, rủi ro về sức khỏe và thu nhập ổn định")
        if input_data.get("dependents", 0) >= 3 and income < 15:
            risk_reasons.append("Gánh nặng người phụ thuộc lớn so với mức thu nhập")

        if risk_reasons and avg_risk >= 0.4:
            advice_list.append("\n**⚠️ Lý do rủi ro chính:**")
            for res in risk_reasons:
                advice_list.append(f"{res}")
            advice_list.append("") # Spacer

        # Gợi ý cụ thể dựa trên DTI
        if avg_dti > 45:
            advice_list.append(f"⚠️ Chỉ số DTI ({avg_dti:.1f}%) đang quá ngưỡng an toàn ({target_dti}%)")
            
            # Gợi ý giảm khoản vay
            if avg_rate > 0:
                coeff = (1 + avg_rate) ** loan_term
                suggested_amount = target_monthly * (coeff - 1) / (avg_rate * coeff)
                if suggested_amount < loan_amount:
                    advice_list.append(f"👉 Nên **giảm khoản vay** xuống khoảng **{suggested_amount:.0f} triệu** (thay vì {loan_amount} triệu) để đạt DTI an toàn")
            
            # Gợi ý tăng kỳ hạn (nếu chưa max)
            if loan_term < 240:
                # Tìm n sao cho monthly_payment <= target_monthly
                # target_monthly = amount * r * (1+r)^n / ((1+r)^n - 1)
                # target_monthly * ((1+r)^n - 1) = amount * r * (1+r)^n
                # target_monthly * (1+r)^n - target_monthly = amount * r * (1+r)^n
                # (target_monthly - amount * r) * (1+r)^n = target_monthly
                # (1+r)^n = target_monthly / (target_monthly - amount * r)
                # n = log(target_monthly / (target_monthly - amount * r)) / log(1+r)
                
                if target_monthly > loan_amount * avg_rate:
                    n_needed = np.log(target_monthly / (target_monthly - loan_amount * avg_rate)) / np.log(1 + avg_rate)
                    if n_needed > loan_term:
                        advice_list.append(f"👉 Nên **kéo dài kỳ hạn** lên khoảng **{int(np.ceil(n_needed))} tháng** để giảm áp lực trả nợ")

        if repayment_method == "interest_only" and avg_dti > 40:
            advice_list.append("👉 Ưu tiên phương án **trả góp (Gốc+Lãi)** để giảm dần dư nợ gốc, tránh áp lực trả nợ lớn ở cuối kỳ")

        if not input_data.get("collateral_assets"):
            advice_list.append("👉 Nên bổ sung thêm thông tin về **tài sản đảm bảo** để tăng độ tin cậy cho hồ sơ")

        advice = "\n" + "\n".join(advice_list) if advice_list else "Vui lòng kiểm tra lại thông tin hồ sơ."
        
        return assessment, advice


_predictor: Optional[LoanPredictor] = None


def get_predictor() -> LoanPredictor:
    global _predictor
    if _predictor is None:
        _predictor = LoanPredictor()
    return _predictor


def reload_predictor():
    global _predictor
    _predictor = LoanPredictor()
    _predictor.load_models()
    return _predictor
