# TestSession — phiên làm bài test DISC của ứng viên (port flow từ SmartHire test_links)
# Mỗi lần gửi bài test cho ứng viên = 1 session có token riêng, hết hạn theo giờ.

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedBase


class TestSession(TenantScopedBase):
    __tablename__ = "test_sessions"

    # Tránh pytest collect nhầm class tên Test* khi import vào file test
    __test__ = False

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Token trong URL làm bài: /test/{token} — unique toàn hệ thống
    token: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Câu trả lời gốc (lưu để audit/tính lại khi cần)
    disc_answers: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    personality_answers: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Kết quả chấm điểm (DISC engine port từ SmartHire)
    disc_scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    disc_primary: Mapped[str | None] = mapped_column(String(1), nullable=True)
    disc_secondary: Mapped[str | None] = mapped_column(String(1), nullable=True)
    disc_profile: Mapped[str | None] = mapped_column(String(5), nullable=True)
    personality_scores: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    analysis: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ai_suggestions: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<TestSession {self.token[:8]}… (used={self.is_used})>"
