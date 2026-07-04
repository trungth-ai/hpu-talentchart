# Migration: tạo bảng test_sessions (bài test DISC) + RLS
# Revision: 0003

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "test_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(80), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disc_answers", postgresql.JSONB(), nullable=True),
        sa.Column("personality_answers", postgresql.JSONB(), nullable=True),
        sa.Column("disc_scores", postgresql.JSONB(), nullable=True),
        sa.Column("disc_primary", sa.String(1), nullable=True),
        sa.Column("disc_secondary", sa.String(1), nullable=True),
        sa.Column("disc_profile", sa.String(5), nullable=True),
        sa.Column("personality_scores", postgresql.JSONB(), nullable=True),
        sa.Column("analysis", postgresql.JSONB(), nullable=True),
        sa.Column("ai_suggestions", postgresql.JSONB(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("recommendation", sa.String(10), nullable=True),
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
    op.create_index(
        "idx_test_sessions_organization_id", "test_sessions", ["organization_id"]
    )
    op.create_index("idx_test_sessions_candidate_id", "test_sessions", ["candidate_id"])
    op.create_index("idx_test_sessions_token", "test_sessions", ["token"], unique=True)

    # RLS — cùng pattern migration 0001/0002
    op.execute("ALTER TABLE test_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE test_sessions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_test_sessions ON test_sessions
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.current_org_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_test_sessions ON test_sessions")
    op.drop_table("test_sessions")
