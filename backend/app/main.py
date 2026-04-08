from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import time
import traceback
from .config import API_PREFIX, PROJECT_NAME, PROJECT_VERSION
from .logging_config import setup_logging, get_logger
from .database import init_db, SessionLocal
from .routers import customers, loan_packages, predictions, dashboard, auth
from .ml.data_generator import LOAN_PACKAGES
from .models.loan_package import LoanPackage

setup_logging()
logger = get_logger("app.main")


from .models.user import User
from .auth_utils import get_password_hash

def seed_users():
    db = SessionLocal()
    try:
        count = db.query(User).count()
        if count == 0:
            users = [
                User(
                    username="manager",
                    password_hash=get_password_hash("manager123"),
                    role="manager",
                    full_name="Quản trị viên"
                ),
                User(
                    username="staff",
                    password_hash=get_password_hash("staff123"),
                    role="staff",
                    full_name="Nhân viên tư vấn"
                )
            ]
            db.add_all(users)
            db.commit()
            print("[OK] Seeded default users: manager/manager123, staff/staff123")
    finally:
        db.close()

def seed_loan_packages():
    db = SessionLocal()
    try:
        count = db.query(LoanPackage).count()
        if count == 0:
            for pkg_data in LOAN_PACKAGES:
                pkg = LoanPackage(
                    name=pkg_data["name"],
                    purpose=pkg_data["purpose"],
                    min_amount=pkg_data["min_amount"],
                    max_amount=pkg_data["max_amount"],
                    base_interest_rate=pkg_data["base_interest_rate"],
                    floating_rate=pkg_data["floating_rate"],
                    min_term_months=pkg_data["min_term_months"],
                    max_term_months=pkg_data["max_term_months"],
                    promotion_months=pkg_data["promotion_months"],
                    promotion_rate=pkg_data["promotion_rate"],
                    description=pkg_data["description"],
                )
                db.add(pkg)
            db.commit()
            print(f"[OK] Seeded {len(LOAN_PACKAGES)} loan packages")
    finally:
        db.close()


app = FastAPI(
    title=PROJECT_NAME,
    version=PROJECT_VERSION,
    description="Hệ thống tư vấn gói vay thông minh sử dụng Machine Learning. "
                "Đề xuất gói vay phù hợp và đánh giá rủi ro vỡ nợ dựa trên đặc trưng khách hàng.",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"{method} {path} - Status: {response.status_code} - Completed in {process_time:.2f}ms"
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"{method} {path} - FAILED after {process_time:.2f}ms")
        logger.error(f"Error detail: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}"}
        )

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(loan_packages.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(dashboard.router, prefix=API_PREFIX)


@app.on_event("startup")
async def startup_event():
    init_db()
    seed_users()
    seed_loan_packages()
    print(f"[STARTED] {PROJECT_NAME} v{PROJECT_VERSION} started!")
    print(f"[DOCS] API Docs: http://localhost:3000{API_PREFIX}/docs")


@app.get("/")
async def root():
    return {
        "name": PROJECT_NAME,
        "version": PROJECT_VERSION,
        "docs": f"{API_PREFIX}/docs",
        "endpoints": {
            "predict": f"{API_PREFIX}/predictions/recommend",
            "packages": f"{API_PREFIX}/packages",
            "dashboard": f"{API_PREFIX}/dashboard/stats",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
