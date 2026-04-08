
# ============ GÓI VAY MẪU ============
LOAN_PACKAGES = [
    {
        "id": 1, "name": "BĐS Ưu đãi 10 năm", "purpose": "bds",
        "min_amount": 500, "max_amount": 10000,
        "base_interest_rate": 8.5, "floating_rate": 11.0,
        "min_term_months": 60, "max_term_months": 300,
        "promotion_months": 18, "promotion_rate": 6.5,
        "description": "Gói vay mua BĐS dài hạn, ưu đãi 18 tháng đầu"
    },
    {
        "id": 2, "name": "BĐS Linh hoạt 5 năm", "purpose": "bds",
        "min_amount": 300, "max_amount": 3000,
        "base_interest_rate": 9.0, "floating_rate": 11.5,
        "min_term_months": 36, "max_term_months": 180,
        "promotion_months": 12, "promotion_rate": 7.0,
        "description": "Gói vay BĐS trung hạn, linh hoạt trả nợ"
    },
    {
        "id": 3, "name": "BĐS Siêu ưu đãi", "purpose": "bds",
        "min_amount": 1000, "max_amount": 13000,
        "base_interest_rate": 7.9, "floating_rate": 10.5,
        "min_term_months": 120, "max_term_months": 360,
        "promotion_months": 24, "promotion_rate": 5.9,
        "description": "Gói vay BĐS cao cấp, ưu đãi 24 tháng, yêu cầu thu nhập cao"
    },
    {
        "id": 4, "name": "Ô tô An tâm", "purpose": "o_to",
        "min_amount": 200, "max_amount": 3000,
        "base_interest_rate": 9.5, "floating_rate": 12.0,
        "min_term_months": 12, "max_term_months": 84,
        "promotion_months": 6, "promotion_rate": 7.5,
        "description": "Gói vay mua ô tô, lãi suất cạnh tranh"
    },
    {
        "id": 5, "name": "Ô tô Linh hoạt", "purpose": "o_to",
        "min_amount": 100, "max_amount": 2000,
        "base_interest_rate": 10.0, "floating_rate": 12.5,
        "min_term_months": 12, "max_term_months": 60,
        "promotion_months": 3, "promotion_rate": 8.0,
        "description": "Gói vay ô tô ngắn hạn, phê duyệt nhanh"
    },
    {
        "id": 6, "name": "Tiêu dùng Ưu đãi", "purpose": "tieu_dung",
        "min_amount": 50, "max_amount": 500,
        "base_interest_rate": 12.0, "floating_rate": 15.0,
        "min_term_months": 6, "max_term_months": 60,
        "promotion_months": 3, "promotion_rate": 9.5,
        "description": "Gói vay tiêu dùng cá nhân, ưu đãi ngắn hạn"
    },
    {
        "id": 7, "name": "Tiêu dùng Tín chấp", "purpose": "tieu_dung",
        "min_amount": 20, "max_amount": 300,
        "base_interest_rate": 14.0, "floating_rate": 18.0,
        "min_term_months": 6, "max_term_months": 36,
        "promotion_months": 0, "promotion_rate": 0,
        "description": "Gói vay tín chấp, không cần tài sản đảm bảo"
    },
    {
        "id": 8, "name": "Kinh doanh SME", "purpose": "kinh_doanh",
        "min_amount": 500, "max_amount": 10000,
        "base_interest_rate": 9.0, "floating_rate": 12.0,
        "min_term_months": 12, "max_term_months": 120,
        "promotion_months": 12, "promotion_rate": 7.0,
        "description": "Gói vay kinh doanh cho doanh nghiệp nhỏ và vừa"
    },
    {
        "id": 9, "name": "Kinh doanh Startup", "purpose": "kinh_doanh",
        "min_amount": 100, "max_amount": 3000,
        "base_interest_rate": 10.5, "floating_rate": 13.0,
        "min_term_months": 12, "max_term_months": 60,
        "promotion_months": 6, "promotion_rate": 8.0,
        "description": "Gói vay cho doanh nghiệp khởi nghiệp"
    },
    {
        "id": 10, "name": "BĐS Trẻ", "purpose": "bds",
        "min_amount": 200, "max_amount": 3000,
        "base_interest_rate": 8.8, "floating_rate": 11.0,
        "min_term_months": 60, "max_term_months": 240,
        "promotion_months": 12, "promotion_rate": 6.8,
        "description": "Gói vay BĐS dành cho người trẻ, thu nhập vừa phải"
    },
]

PURPOSES = ["bds", "o_to", "tieu_dung", "kinh_doanh"]
