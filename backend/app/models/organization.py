# Organization — bảng ROOT của hệ thống multi-tenant (KHÔNG tenant-scoped)
# Mỗi organization = 1 tenant (trường ĐH/CĐ hoặc HR agency)

import uuid
from typing import Any

from sqlalchemy import JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


def _default_settings() -> dict[str, Any]:
    # Eastern Layer mặc định TẮT — chỉ hiện Behavioural Layer (Critical Business Rules)
    return {"eastern_layer_enabled": False}


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # slug dùng làm subdomain: {slug}.talentchart.hpu.edu.vn — unique toàn hệ thống
    slug: Mapped[str] = mapped_column(String(63), unique=True, index=True, nullable=False)

    # Cấu hình theo tenant (VD: bật/tắt Eastern Layer)
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON, default=_default_settings, nullable=False
    )

    # Soft delete: active | inactive
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    def __repr__(self) -> str:
        return f"<Organization {self.slug}: {self.name}>"
