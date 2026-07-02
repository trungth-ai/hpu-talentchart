# ★ Base models — TenantScopedBase là nền tảng multi-tenant (ADR-003)
# Mọi bảng chứa dữ liệu khách hàng PHẢI inherit TenantScopedBase.
# Chỉ bảng root (organizations) mới inherit Base trực tiếp.

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """Declarative base chung cho mọi model."""


class TimestampMixin:
    """created_at/updated_at — bắt buộc cho mọi bảng (db-conventions.md)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantScopedBase(TimestampMixin, Base):
    """★ Base cho MỌI bảng dữ liệu tenant (CRITICAL — xem .claude/rules/tenant-isolation.md).

    Cung cấp sẵn: id (UUID), organization_id (NOT NULL + index), status (soft delete),
    created_at, updated_at. Query tự động được filter theo organization_id
    qua event listener trong database.py.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Soft delete: active | inactive (KHÔNG BAO GIỜ hard delete — rules/soft-delete.md)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    @declared_attr
    def organization_id(cls) -> Mapped[uuid.UUID]:  # noqa: N805
        # NOT NULL + index — quy tắc số 1 của tenant isolation
        return mapped_column(
            Uuid(as_uuid=True),
            ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
