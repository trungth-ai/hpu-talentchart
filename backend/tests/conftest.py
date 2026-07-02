# Test fixtures — SQLite in-memory (aiosqlite) thay PostgreSQL để test nhanh
# LƯU Ý: RLS (lớp bảo vệ số 3) chỉ có trên PostgreSQL — được verify riêng trên staging.
# Test ở đây verify lớp 1 (middleware) + lớp 2 (event listener auto-filter).

import os

# ★ Env phải set TRƯỚC khi import app (config dùng lru_cache, engine tạo lúc import)
os.environ["JWT_SECRET"] = "test-secret-key-du-dai-32-ky-tu-tro-len-cho-jwt"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["APP_ENV"] = "development"
os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"
os.environ["BCRYPT_ROUNDS"] = "4"  # cost thấp cho test chạy nhanh (production = 12)

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, hash_password
from app.database import async_session_factory, engine
from app.main import app
from app.middleware.rate_limit import limiter
from app.models import Base, Organization, User

BASE_URL = "http://app.talentchart.hpu.edu.vn"


@pytest.fixture(autouse=True)
async def setup_database():
    """Tạo schema sạch cho mỗi test + reset rate limiter."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    limiter.reset()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def org_a(db_session):
    org = Organization(name="Trường ĐH Hải Phòng", slug="hpu")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def org_b(db_session):
    org = Organization(name="HR Agency Alpha", slug="alpha")
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


def _make_user(org, email: str, org_role: str = "hr_manager") -> User:
    return User(
        organization_id=org.id,
        email=email,
        username=email.split("@")[0],
        full_name="Người Dùng Test",
        hashed_password=hash_password("MatKhau@123"),
        org_role=org_role,
    )


@pytest.fixture
async def hr_manager_org_a(db_session, org_a):
    user = _make_user(org_a, "hr.a@hpu.edu.vn")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def hr_manager_org_b(db_session, org_b):
    user = _make_user(org_b, "hr.b@alpha.vn")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def member_org_a(db_session, org_a):
    user = _make_user(org_a, "member.a@hpu.edu.vn", org_role="member")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
        yield client


def auth_headers(user: User) -> dict[str, str]:
    """Header Authorization với access token thật của user."""
    return {"Authorization": f"Bearer {create_access_token(user)}"}
