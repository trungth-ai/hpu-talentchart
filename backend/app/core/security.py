# Security — JWT (access 15 phút / refresh 7 ngày) + bcrypt cost 12 (PLAN.md Sprint 1)

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
from app.exceptions import UnauthorizedError

settings = get_settings()


def hash_password(plain_password: str) -> str:
    """Hash mật khẩu bằng bcrypt (cost lấy từ settings, mặc định 12)."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """So khớp mật khẩu — trả False thay vì raise để không leak thông tin."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def _create_token(claims: dict[str, Any], expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {**claims, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user) -> str:
    """Access token chứa: user_id, organization_id, org_role, system_role (PLAN.md Story 1)."""
    return _create_token(
        {
            "sub": str(user.id),
            "organization_id": str(user.organization_id),
            "org_role": user.org_role,
            "system_role": user.system_role,
            "type": "access",
        },
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user) -> str:
    """Refresh token chỉ chứa định danh tối thiểu — không chứa role."""
    return _create_token(
        {
            "sub": str(user.id),
            "organization_id": str(user.organization_id),
            "type": "refresh",
        },
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Giải mã + validate JWT. Sai loại token / hết hạn / chữ ký sai → 401."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise UnauthorizedError("Token không hợp lệ hoặc đã hết hạn") from exc
    if payload.get("type") != expected_type:
        raise UnauthorizedError("Loại token không hợp lệ")
    return payload
