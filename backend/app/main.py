# FastAPI app — entry point
# Thứ tự middleware (Starlette chạy middleware add SAU trước):
#   AuthMiddleware (decode JWT) → TenantMiddleware (resolve org) → router

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.core.responses import error
from app.exceptions import AppException
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import limiter
from app.middleware.tenant import TenantMiddleware
from app.routers import (
    auth,
    campaigns,
    candidates,
    epa,
    job_posts,
    public_candidates,
    public_careers,
    public_tests,
    test_links,
    users,
)

app = FastAPI(
    title="TalentChart API",
    description="Nền tảng SaaS tuyển dụng & đánh giá nhân sự tích hợp EPA",
    version="0.1.0",
)

# Rate limiter (slowapi) cần gắn vào app.state
app.state.limiter = limiter

# Middleware — add TenantMiddleware TRƯỚC để AuthMiddleware (add sau) chạy trước
app.add_middleware(TenantMiddleware)
app.add_middleware(AuthMiddleware)

# CORS — frontend admin (localhost:3000 dev) + mọi subdomain tenant (production)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(job_posts.router, prefix="/api/v1")
app.include_router(test_links.router, prefix="/api/v1")
app.include_router(epa.router, prefix="/api/v1")
app.include_router(public_careers.router, prefix="/api/v1")
app.include_router(public_tests.router, prefix="/api/v1")
app.include_router(public_candidates.router, prefix="/api/v1")


# ─── Exception handlers — mọi lỗi đều trả envelope chuẩn ───


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content=error(exc.message, code=exc.code, errors=exc.errors),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # Chuyển lỗi Pydantic sang format {field, message} tiếng Việt
    errors = [
        {
            "field": ".".join(str(loc) for loc in e["loc"] if loc != "body"),
            "message": e["msg"],
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error("Dữ liệu không hợp lệ", code="VALIDATION_ERROR", errors=errors),
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=error("Quá nhiều yêu cầu, vui lòng thử lại sau", code="RATE_LIMIT"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # KHÔNG expose stack trace ra ngoài (api-conventions.md)
    return JSONResponse(
        status_code=500,
        content=error("Lỗi hệ thống, vui lòng thử lại sau", code="INTERNAL_ERROR"),
    )


@app.get("/health", tags=["system"])
async def health() -> dict:
    """Healthcheck cho Docker/Caddy."""
    return {"status": "ok", "service": "talentchart-backend"}
