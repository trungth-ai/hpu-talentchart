# Auth router — POST /auth/login, POST /auth/refresh, GET /auth/me (PLAN.md Story 1)
# Login scoped theo tổ chức: tenant middleware phải resolve được org
# (qua subdomain hoặc X-Org-Slug dev) TRƯỚC khi login.

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_current_user
from app.core.responses import success
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.core.tenant_context import (
    get_current_org_id,
    reset_current_org_id,
    set_current_org_id,
)
from app.database import get_db, set_rls_guc
from app.exceptions import BusinessRuleError, UnauthorizedError
from app.middleware.rate_limit import LOGIN_RATE_LIMIT, limiter
from app.models.user import User
from app.schemas.auth import LoginData, LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


@router.post("/login")
@limiter.limit(LOGIN_RATE_LIMIT)  # 5 lần/phút/IP — chống brute-force
async def login(
    request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)
):
    org_id = get_current_org_id()
    if org_id is None:
        # Không xác định được tổ chức → không thể login (login luôn scoped theo org)
        raise BusinessRuleError(
            "Không xác định được tổ chức — truy cập qua địa chỉ của tổ chức bạn"
        )

    # Email unique trong phạm vi organization (auto-filter + explicit filter)
    result = await db.execute(
        select(User)
        .where(User.email == data.email.lower())
        .where(User.organization_id == org_id)
        .where(User.status == "active")
    )
    user = result.scalar_one_or_none()

    # Thông báo chung chung — không leak email có tồn tại hay không
    if user is None or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Email hoặc mật khẩu không đúng")

    user.last_login_at = datetime.now(UTC)
    tokens = _issue_tokens(user)

    return success(
        LoginData(**tokens.model_dump(), user=UserResponse.model_validate(user)).model_dump(),
        message="Đăng nhập thành công",
    )


@router.post("/refresh")
async def refresh(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token, expected_type="refresh")

    # Middleware không resolve được tenant từ body → set context từ chính refresh token
    # (token đã được verify chữ ký ở trên) để auto-filter + RLS hoạt động đúng
    try:
        org_id = UUID(payload["organization_id"])
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError() from exc

    ctx_token = set_current_org_id(org_id)
    try:
        await set_rls_guc(db)
        result = await db.execute(
            select(User)
            .where(User.id == UUID(payload["sub"]))
            .where(User.organization_id == org_id)
            .where(User.status == "active")
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise UnauthorizedError()
        tokens = _issue_tokens(user)
    finally:
        reset_current_org_id(ctx_token)

    return success(tokens.model_dump(), message="Làm mới token thành công")


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return success(UserResponse.model_validate(user).model_dump(mode="json"))
