# Cấu hình ứng dụng — Settings fail-fast
# JWT_SECRET BẮT BUỘC phải có trong env, KHÔNG có giá trị default (xem CLAUDE.md Gotchas)

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Môi trường: development | staging | production
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database — async cho app, sync cho Alembic
    DATABASE_URL: str = "postgresql+asyncpg://talentchart:talentchart@localhost:5432/talentchart"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://talentchart:talentchart@localhost:5432/talentchart"

    # Redis (cache, rate limit, Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    # Rate limit storage: "memory://" cho dev/test, dùng REDIS_URL cho production
    RATE_LIMIT_STORAGE_URI: str = "memory://"

    # JWT — KHÔNG có default, thiếu là app không khởi động được (fail-fast)
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Bcrypt cost (theo PLAN.md Sprint 1)
    BCRYPT_ROUNDS: int = 12

    # Google OAuth (ADR-004) — rỗng = tắt đăng nhập Google
    GOOGLE_CLIENT_ID: str = ""

    # Claude API — rỗng = narrative dùng template, không gọi API (ADR-005)
    ANTHROPIC_API_KEY: str = ""
    # TTL token của ứng viên (type=candidate)
    CANDIDATE_TOKEN_EXPIRE_MINUTES: int = 60

    # Domain gốc để resolve tenant theo subdomain: {org-slug}.talentchart.hpu.edu.vn
    BASE_DOMAIN: str = "talentchart.hpu.edu.vn"

    # CORS — dev cho phép localhost:3000; production set qua env (phân cách dấu phẩy)
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_origin_regex(self) -> str:
        # Cho phép mọi subdomain tenant: https://{slug}.talentchart.hpu.edu.vn
        return rf"https://([a-z0-9-]+\.)?{self.BASE_DOMAIN.replace('.', r'\.')}"
    # Các subdomain hệ thống, KHÔNG phải slug của tenant
    RESERVED_SUBDOMAINS: frozenset[str] = frozenset({"app", "www", "storage", "api"})

    @field_validator("JWT_SECRET")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        # Chặn secret rỗng/quá ngắn/giá trị placeholder thường gặp
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET phải có ít nhất 32 ký tự (random)")
        if v.lower() in {"secret", "changeme", "your-secret-key"}:
            raise ValueError("JWT_SECRET không được dùng giá trị placeholder")
        return v

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    # lru_cache để chỉ đọc env 1 lần; fail ngay khi import nếu thiếu JWT_SECRET
    return Settings()
