# Migration: thêm cột gender vào candidates (dùng cho so sánh tương hợp theo giới).
# Revision: 0007

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("gender", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "gender")
