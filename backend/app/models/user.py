# User — tài khoản người dùng, tenant-scoped
# Email/username unique TRONG PHẠM VI organization, KHÔNG unique toàn hệ thống
# (Critical Business Rules — CLAUDE.md)

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class User(TenantScopedBase):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        UniqueConstraint("organization_id", "username", name="uq_users_org_username"),
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # bcrypt hash (cost 12) — không bao giờ trả về trong response
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)

    # Vai trò trong tổ chức: owner | admin | hr_manager | recruiter | member
    org_role: Mapped[str] = mapped_column(String(30), default="member", nullable=False)

    # Vai trò cấp hệ thống (platform): user | super_admin
    system_role: Mapped[str] = mapped_column(String(30), default="user", nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.org_role})>"
