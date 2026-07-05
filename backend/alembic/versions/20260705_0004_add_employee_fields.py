# Migration: thêm employee_code + department vào candidates (hợp nhất nhân sự)
# Revision: 0004

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("employee_code", sa.String(20), nullable=True))
    op.add_column("candidates", sa.Column("department", sa.String(100), nullable=True))
    op.create_index("idx_candidates_department", "candidates", ["department"])


def downgrade() -> None:
    op.drop_index("idx_candidates_department", table_name="candidates")
    op.drop_column("candidates", "department")
    op.drop_column("candidates", "employee_code")
