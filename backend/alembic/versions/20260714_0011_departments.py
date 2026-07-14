# Migration: cơ cấu tổ chức — bảng departments (cây + trưởng đơn vị) + candidates.department_id.
# Tenant-scoped + RLS (cùng pattern 0002). Chỉ DDL, không ghi dữ liệu → không vướng RLS lúc chạy.
# Revision 0011.

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "manager_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_departments_organization_id", "departments", ["organization_id"])
    op.create_index("idx_departments_parent_id", "departments", ["parent_id"])
    op.execute("ALTER TABLE departments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE departments FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_departments ON departments
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.current_org_id', true)::uuid)
        """
    )

    op.add_column(
        "candidates",
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_candidates_department_id", "candidates", ["department_id"])


def downgrade() -> None:
    op.drop_index("idx_candidates_department_id", table_name="candidates")
    op.drop_column("candidates", "department_id")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_departments ON departments")
    op.drop_table("departments")
