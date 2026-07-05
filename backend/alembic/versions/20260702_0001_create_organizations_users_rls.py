# Migration: tạo bảng organizations + users, bật Row Level Security (ADR-003)
# Revision: 0001
#
# ⚠️ RLS là lớp bảo vệ số 3 (safety-net cuối) — policy dựa trên biến session
# app.current_org_id do app set qua set_config() trong database.py (SET LOCAL).
# FORCE ROW LEVEL SECURITY để cả table owner (user talentchart) cũng bị áp policy.
# Phần RLS này cần Trung review trước khi merge (theo PLAN.md).

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ─── organizations — bảng root, KHÔNG tenant-scoped, KHÔNG bật RLS ───
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(63), nullable=False),
        sa.Column(
            "settings",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{\"eastern_layer_enabled\": false}'::jsonb"),
        ),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_organizations_slug", "organizations", ["slug"], unique=True)

    # ─── users — tenant-scoped (TenantScopedBase) ───
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(100), nullable=False),
        sa.Column("org_role", sa.String(30), nullable=False, server_default="member"),
        sa.Column("system_role", sa.String(30), nullable=False, server_default="user"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        # Email/username unique TRONG org, không unique toàn hệ thống (CLAUDE.md)
        sa.UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        sa.UniqueConstraint("organization_id", "username", name="uq_users_org_username"),
    )
    op.create_index("idx_users_organization_id", "users", ["organization_id"])
    op.create_index("idx_users_email", "users", ["email"])

    # ─── ★ Row Level Security cho users (lớp bảo vệ số 3 — ADR-003) ───
    # Policy: chỉ thấy/ghi được row có organization_id = app.current_org_id.
    # current_setting(..., true) → NULL khi chưa set → không match row nào (deny by default).
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_users ON users
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.current_org_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_organization_id", table_name="users")
    op.drop_table("users")
    op.drop_index("idx_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
