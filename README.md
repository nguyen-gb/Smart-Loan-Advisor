# 🏦 Smart Loan Advisor

Hệ thống tư vấn gói vay thông minh sử dụng Machine Learning. Đề xuất gói vay phù hợp và đánh giá rủi ro vỡ nợ dựa trên dữ liệu khách hàng thực tế.

## 📋 Tổng quan

### Vấn đề
Nhân viên ngân hàng tư vấn gói vay dựa vào kinh nghiệm cá nhân, dẫn đến:
- Tư vấn không nhất quán giữa các nhân viên
- Khó cân bằng giữa ưu đãi và rủi ro vỡ nợ
- Mất thời gian phân tích thủ công

### Giải pháp
Hệ thống ML tinh gọn:
1. **Đề xuất gói vay phù hợp** (Random Forest) - Top 3 gói với độ tin cậy cao nhất.
2. **Đánh giá rủi ro vỡ nợ** (Gradient Boosting) - Phân tích dựa trên thu nhập, khoản vay và lịch sử thanh toán.
3. **Huấn luyện linh hoạt** - Cho phép nhập dữ liệu từ file CSV/Excel để cập nhật mô hình theo thực tế.

## 🛠 Công nghệ

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.10+) |
| ML | Scikit-learn (Random Forest, Gradient Boosting) |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | HTML/CSS/JS (Vanilla) - Premium Banking UI |
| Data Processing | Pandas, NumPy, Openpyxl |

## 📁 Cấu trúc dự án

```
SmartLoanAdvisor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Cấu hình hệ thống
│   │   ├── database.py          # Kết nối Database
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas (Validation)
│   │   ├── routers/             # API endpoints (Auth, ML, Loan...)
│   │   ├── ml/                  # Machine Learning Pipeline
│   │   │   ├── data_generator.py   # Hằng số và danh sách gói vay
│   │   │   ├── preprocessor.py     # Tiền xử lý dữ liệu (Feature Engineering)
│   │   │   ├── trainer.py          # Huấn luyện model từ dữ liệu import
│   │   │   └── predictor.py        # Logic dự báo và đánh giá
│   │   └── services/            # Business logic (LoanService)
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Main Dashboard UI
│   ├── login.html               # Trang đăng nhập
│   ├── css/style.css            # Custom CSS (Modern Dark/Light theme)
│   └── js/app.js                # Frontend core logic
└── README.md
```

## 🚀 Cài đặt & Chạy

### 1. Cài đặt dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Chạy server

```bash
cd backend
python -m uvicorn app.main:app --reload --port 3000
```

### 3. Huấn luyện ML Models

Hệ thống yêu cầu huấn luyện mô hình bằng dữ liệu thực tế trước khi sử dụng:
- **Giao diện**: Vào mục **ML Models** -> **Huấn luyện từ File Import**.
- **Định dạng**: Upload file `.csv` hoặc `.xlsx` chứa các trường dữ liệu cần thiết (age, monthly_income, loan_amount, is_on_time_payment, ...).
- **Yêu cầu**: Tối thiểu 50 bản ghi để đảm bảo độ chính xác.

### 4. Sử dụng

- **Frontend**: [http://localhost:3000/static/index.html](http://localhost:3000/static/index.html)
- **API Docs**: [http://localhost:3000/api/v1/docs](http://localhost:3000/api/v1/docs)

## 📊 Dữ liệu & Tính năng

Hệ thống hỗ trợ quản lý 10 gói vay mẫu mặc định từ BĐS, Ô tô đến Tiêu dùng và Kinh doanh. Mỗi gói vay có các thông số lãi suất, ưu đãi và thời hạn khác nhau để Model Machine Learning phân tích sự phù hợp.

## 🤖 Machine Learning

### Model 1: Package Recommender (Random Forest)
- Tuyển chọn gói vay phù hợp nhất dựa trên đặc trưng nhân khẩu học và nhu cầu tài chính.
- Sử dụng các đặc trưng: `age`, `gender`, `marital_status`, `monthly_income`, `purpose`, `loan_amount`, `loan_term_months`.

### Model 2: Risk Assessor (Gradient Boosting)
- Dự báo xác suất vỡ nợ (Risk Score) từ 0 đến 1.
- Phân loại mức rủi ro: **Thấp**, **Trung bình**, **Cao** để hỗ trợ duyệt hồ sơ.

### Feature Engineering
Hệ thống tự động tính toán các chỉ số quan trọng:
- **DTI Ratio**: Tỉ lệ nợ trên thu nhập.
- **Loan-Income Ratio**: Tỉ lệ khoản vay trên thu nhập.

## 📡 API Endpoints (v1)

| Method | Endpoint | Mô tả | Quyền |
|--------|----------|-------|-------|
| POST | `/api/v1/auth/login` | Đăng nhập hệ thống | Public |
| POST | `/api/v1/predictions/recommend` | Dự báo gói vay phù hợp | Staff/Manager |
| POST | `/api/v1/predictions/apply` | Tạo hồ sơ vay mới | Staff/Manager |
| GET | `/api/v1/predictions/applications` | Danh sách hồ sơ vay | Manager |
| PUT | `/api/v1/predictions/applications/{id}/status` | Duyệt/Từ chối hồ sơ | Manager |
| GET | `/api/v1/packages/` | Xem danh sách gói vay | Staff/Manager |
| GET | `/api/v1/dashboard/ml/status` | Kiểm tra trạng thái Model | Manager |
| POST | `/api/v1/dashboard/ml/train-upload` | Huấn luyện Model từ file | Manager |
