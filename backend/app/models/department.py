# Cơ cấu tổ chức — phòng ban dạng CÂY (parent_id) + trưởng đơn vị (manager_user_id).
# Tenant-scoped: mỗi tổ chức có cây phòng ban riêng (inherit TenantScopedBase + RLS).

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class Department(TenantScopedBase):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Phòng cha (None = cấp cao nhất) — tạo cây nhiều cấp
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Trưởng đơn vị (1 user trong tổ chức)
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<Department {self.name}>"
