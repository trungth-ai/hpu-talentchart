# Candidate — hợp nhất applicant/employee/student/alumni qua candidate_type
# (Critical Business Rules — KHÔNG tách bảng riêng)
#
# Pipeline 5 trạng thái (gộp từ 8 — ADR-008), đi TIẾN tuần tự:
#   RECEIVED (Tiếp nhận) → ASSESSMENT (Đánh giá) → INTERVIEW (Phỏng vấn) → HIRED/REJECTED
# REJECTED chuyển tới được từ mọi bước chưa kết thúc (ADR-007).
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

# Pipeline — gộp còn 5 trạng thái (ADR-008); thứ tự TIẾN bắt buộc
PIPELINE_STAGES = (
    "RECEIVED",    # Tiếp nhận (gộp NEW + SCREENING)
    "ASSESSMENT",  # Đánh giá — làm bài test DISC (gộp TEST_SENT + TEST_DONE)
    "INTERVIEW",   # Phỏng vấn (gộp INTERVIEW + DECISION)
    "HIRED",
    "REJECTED",
)
TERMINAL_STAGES = ("HIRED", "REJECTED")


class Candidate(TenantScopedBase):
    __tablename__ = "candidates"

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    candidate_type: Mapped[str] = mapped_column(
        String(20), default="applicant", nullable=False
    )

    # Dành cho candidate_type=employee (hợp nhất nhân sự từ Fortune HR/SmartHire)
    employee_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Giới tính: 'male' | 'female' | None — dùng so sánh tương hợp cho tinh tế
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Pipeline tuyển dụng — chuyển trạng thái qua service, KHÔNG set trực tiếp từ API
    pipeline_stage: Mapped[str] = mapped_column(String(20), default="RECEIVED", nullable=False)

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
    # Phòng ban (cơ cấu tổ chức) — gán nhân sự vào đơn vị
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
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
