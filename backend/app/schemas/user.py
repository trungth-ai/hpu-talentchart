# User schemas — Response KHÔNG include organization_id (tránh leak — rule số 6)

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

_VALID_ROLES = frozenset({"owner", "admin", "hr_manager", "recruiter", "member"})
_VALID_STATUS = frozenset({"active", "inactive"})


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    org_role: str
    system_role: str
    status: str
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminUpdate(BaseModel):
    """Admin đổi vai trò và/hoặc khóa-mở người dùng (chỉ owner/admin)."""

    org_role: str | None = None
    status: str | None = None

    @field_validator("org_role")
    @classmethod
    def role_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_ROLES:
            raise ValueError(f"Vai trò không hợp lệ (chọn: {', '.join(sorted(_VALID_ROLES))})")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in _VALID_STATUS:
            raise ValueError("Trạng thái chỉ nhận 'active' hoặc 'inactive'")
        return v
