# Campaign — đợt tuyển dụng (Sprint 2-3, ATS Core)

from datetime import date

from sqlalchemy import Date, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase

# Trạng thái nghiệp vụ của campaign (ngoài inactive = soft delete)
CAMPAIGN_STATUSES = ("draft", "open", "closed", "inactive")


class Campaign(TenantScopedBase):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    target_headcount: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Lương LUÔN Integer VNĐ — KHÔNG Float (rules/money-integer.md)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # status kế thừa từ TenantScopedBase, dùng thêm giá trị: draft | open | closed

    def __repr__(self) -> str:
        return f"<Campaign {self.name} ({self.status})>"
