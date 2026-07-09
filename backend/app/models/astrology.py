# Bảng tham chiếu tử vi (con giáp + cung hoàng đạo) — dữ liệu TOÀN CỤC (read-only reference).
# KHÔNG tenant-scoped, KHÔNG RLS: inherit Base trực tiếp (giống organizations là bảng root).
# Nạp nội dung đầy đủ từ tài liệu nguồn bằng scripts/seed_astrology.py.

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AstrologyReference(Base):
    __tablename__ = "astrology_reference"

    # kind: 'zodiac' (con giáp) | 'horoscope' (cung hoàng đạo)
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)
    # key: địa chi (Tý, Sửu, ...) cho zodiac; code cung (ARIES, ...) cho horoscope
    key: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    # content: JSON đầy đủ (nguyên văn theo mục) — cấu trúc tùy kind
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    def __repr__(self) -> str:
        return f"<AstrologyReference {self.kind}:{self.key}>"
