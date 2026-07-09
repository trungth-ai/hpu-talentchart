# Migration: bảng astrology_reference — nội dung tử vi (con giáp + cung hoàng đạo) đầy đủ.
# Toàn cục (read-only reference), KHÔNG tenant-scoped, KHÔNG RLS.
# Revision: 0006

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "astrology_reference",
        sa.Column("kind", sa.String(20), nullable=False),   # 'zodiac' | 'horoscope'
        sa.Column("key", sa.String(20), nullable=False),    # địa chi hoặc code cung
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("kind", "key", name="pk_astrology_reference"),
    )


def downgrade() -> None:
    op.drop_table("astrology_reference")
