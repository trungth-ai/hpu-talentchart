# Candidate — hợp nhất applicant/employee/student/alumni qua candidate_type
# (Critical Business Rules — KHÔNG tách bảng riêng)
#
# Pipeline 7 trạng thái, CHỈ đi tuần tự (không nhảy cóc từ API):
#   NEW → SCREENING → TEST_SENT → TEST_DONE → INTERVIEW → DECISION → HIRED/REJECTED
#
# Dữ liệu ngày/giờ/nơi sinh (phục vụ EPA) là dữ liệu NHẠY CẢM theo NĐ 13/2023/NĐ-CP:
# chỉ lưu khi epa_consent=True (opt-in), có quyền xóa trong 30 ngày.

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase

# Loại candidate (hợp nhất 1 bảng)
CANDIDATE_TYPES = ("applicant", "employee", "student", "alumni")

# Pipeline — thứ tự tuần tự bắt buộc
PIPELINE_STAGES = (
    "NEW",
    "SCREENING",
    "TEST_SENT",
    "TEST_DONE",
    "INTERVIEW",
    "DECISION",
    "HIRED",
    "REJECTED",
)
TERMINAL_STAGES = ("HIRED", "REJECTED")


class Candidate(TenantScopedBase):
    __tablename__ = "candidates"

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    candidate_type: Mapped[str] = mapped_column(
        String(20), default="applicant", nullable=False
    )

    # Pipeline tuyển dụng — chuyển trạng thái qua service, KHÔNG set trực tiếp từ API
    pipeline_stage: Mapped[str] = mapped_column(String(20), default="NEW", nullable=False)

    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Nguồn ứng viên: career_page, referral, import...
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ─── Dữ liệu nhạy cảm cho EPA (NĐ 13/2023) — chỉ lưu khi opt-in ───
    epa_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    epa_consent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_time: Mapped[str | None] = mapped_column(String(5), nullable=True)  # "HH:MM"
    birth_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Candidate {self.full_name} [{self.pipeline_stage}]>"
