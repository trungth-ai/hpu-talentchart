# Bảng tử vi cào từ lichngaytot theo KỲ (ngày/tuần/tháng/năm) × chiều (ngày tốt/con giáp/cung).
# Dữ liệu TOÀN CỤC (shared, dùng chung mọi tổ chức) — KHÔNG tenant-scoped, inherit Base.
# Cào theo lô bằng Celery beat (mỗi kỳ 1 lịch), lưu lại để: hiển thị nhanh (không cào lại mỗi
# lần xem, giảm gọi AI) + xem lại các kỳ trước. Thay cho bảng daily_fortunes (migration 0010).

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FortuneContent(Base):
    __tablename__ = "fortune_content"

    # Kỳ: day | week | month | year
    period_type: Mapped[str] = mapped_column(String(10), primary_key=True)
    # Khóa kỳ: 'YYYY-MM-DD' (day) | 'YYYY-Www' (week) | 'YYYY-MM' (month) | 'YYYY' (year)
    period_key: Mapped[str] = mapped_column(String(20), primary_key=True)
    # kind: day (ngày tốt/xấu, chung) | zodiac (theo tuổi/địa chi) | horoscope (theo cung)
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    # key: '' cho day; địa chi cho zodiac; code cung (CAPRICORN...) cho horoscope
    key: Mapped[str] = mapped_column(String(20), primary_key=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<FortuneContent {self.period_type}:{self.period_key} {self.kind}:{self.key}>"
