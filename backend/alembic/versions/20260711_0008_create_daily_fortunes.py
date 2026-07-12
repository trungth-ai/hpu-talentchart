# Migration: bảng daily_fortunes — tử vi theo ngày cào từ lichngaytot (cache hiển thị + lịch sử).
# Toàn cục (shared reference), KHÔNG tenant-scoped, KHÔNG RLS. Revision 0008.

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_fortunes",
        sa.Column("fortune_date", sa.Date(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),  # day | zodiac_day | horoscope_day
        sa.Column("key", sa.String(20), nullable=False),  # '' | địa chi | code cung
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column(
            "scraped_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("fortune_date", "kind", "key", name="pk_daily_fortunes"),
    )
    op.create_index("ix_daily_fortunes_date", "daily_fortunes", ["fortune_date"])


def downgrade() -> None:
    op.drop_index("ix_daily_fortunes_date", table_name="daily_fortunes")
    op.drop_table("daily_fortunes")
