# Bảng tử vi theo NGÀY cào từ lichngaytot.com — dữ liệu TOÀN CỤC (shared reference).
# KHÔNG tenant-scoped, KHÔNG RLS: inherit Base trực tiếp (giống astrology_reference).
# Được cào theo lô hằng ngày (Celery beat) cho đủ 12 cung + 12 tuổi + ngày tốt/xấu, lưu lại để:
#   - hiển thị nhanh, không phải cào lại mỗi lần xem (giảm tải + giảm gọi AI),
#   - xem lại tử vi các ngày trước (lịch sử lưu trong DB).

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DailyFortune(Base):
    __tablename__ = "daily_fortunes"

    # Ngày dương lịch của nội dung tử vi
    fortune_date: Mapped[date] = mapped_column(Date, primary_key=True)
    # kind: day (ngày tốt/xấu, chung) | zodiac_day (theo tuổi) | horoscope_day (theo cung)
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    # key: '' cho day; địa chi cho zodiac_day; code cung (CAPRICORN...) cho horoscope_day
    key: Mapped[str] = mapped_column(String(20), primary_key=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<DailyFortune {self.fortune_date} {self.kind}:{self.key}>"
