# Migration: tổng quát daily_fortunes -> fortune_content (tử vi theo kỳ ngày/tuần/tháng/năm).
# Tạo bảng mới, chuyển dữ liệu ngày cũ (nếu có) sang period_type='day', rồi bỏ daily_fortunes.
# Revision 0010.

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fortune_content",
        sa.Column("period_type", sa.String(10), primary_key=True),
        sa.Column("period_key", sa.String(20), primary_key=True),
        sa.Column("kind", sa.String(20), primary_key=True),
        sa.Column("key", sa.String(20), primary_key=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    # Chuyển dữ liệu ngày cũ (nếu bảng daily_fortunes tồn tại và có dữ liệu)
    bind = op.get_bind()
    if bind.dialect.has_table(bind, "daily_fortunes"):
        op.execute(
            "INSERT INTO fortune_content "
            "(period_type, period_key, kind, key, source_url, excerpt, scraped_at) "
            "SELECT 'day', CAST(fortune_date AS VARCHAR), "
            "CASE kind WHEN 'zodiac_day' THEN 'zodiac' "
            "WHEN 'horoscope_day' THEN 'horoscope' ELSE kind END, "
            "key, source_url, excerpt, scraped_at FROM daily_fortunes"
        )
        op.drop_table("daily_fortunes")


def downgrade() -> None:
    op.create_table(
        "daily_fortunes",
        sa.Column("fortune_date", sa.Date(), primary_key=True),
        sa.Column("kind", sa.String(20), primary_key=True),
        sa.Column("key", sa.String(20), primary_key=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute(
        "INSERT INTO daily_fortunes (fortune_date, kind, key, source_url, excerpt, scraped_at) "
        "SELECT CAST(period_key AS DATE), "
        "CASE kind WHEN 'zodiac' THEN 'zodiac_day' "
        "WHEN 'horoscope' THEN 'horoscope_day' ELSE kind END, "
        "key, source_url, excerpt, scraped_at FROM fortune_content WHERE period_type = 'day'"
    )
    op.drop_table("fortune_content")
