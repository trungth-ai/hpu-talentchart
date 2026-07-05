# Migration: thêm address vào candidates (đối chiếu từ danh bạ Google Contacts)
# Revision: 0005

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("address", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("candidates", "address")
