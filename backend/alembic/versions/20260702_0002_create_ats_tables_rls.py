# Migration: tạo bảng ATS Core (campaigns, candidates, job_posts) + RLS (Sprint 2-4)
# Revision: 0002
#
# Mọi bảng tenant-scoped đều: organization_id NOT NULL + index, RLS ENABLE + FORCE
# với policy theo app.current_org_id (cùng pattern migration 0001).

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _tenant_columns() -> list[sa.Column]:
    """Cột chung của mọi bảng tenant-scoped (khớp TenantScopedBase)."""
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
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
    ]


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_{table} ON {table}
        USING (organization_id = current_setting('app.current_org_id', true)::uuid)
        WITH CHECK (organization_id = current_setting('app.current_org_id', true)::uuid)
        """
    )


def upgrade() -> None:
    # ─── campaigns ───
    op.create_table(
        "campaigns",
        *_tenant_columns(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("position", sa.String(100), nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("target_headcount", sa.Integer(), nullable=False, server_default="1"),
        # Lương Integer VNĐ (rules/money-integer.md)
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
    )
    op.create_index("idx_campaigns_organization_id", "campaigns", ["organization_id"])
    _enable_rls("campaigns")

    # ─── candidates — bảng hợp nhất applicant/employee/student/alumni ───
    op.create_table(
        "candidates",
        *_tenant_columns(),
        sa.Column("full_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column(
            "candidate_type", sa.String(20), nullable=False, server_default="applicant"
        ),
        sa.Column("pipeline_stage", sa.String(20), nullable=False, server_default="NEW"),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Dữ liệu nhạy cảm EPA — opt-in theo NĐ 13/2023/NĐ-CP
        sa.Column("epa_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("epa_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("birth_time", sa.String(5), nullable=True),
        sa.Column("birth_place", sa.String(255), nullable=True),
    )
    op.create_index("idx_candidates_organization_id", "candidates", ["organization_id"])
    op.create_index("idx_candidates_email", "candidates", ["email"])
    op.create_index("idx_candidates_campaign_id", "candidates", ["campaign_id"])
    op.create_index("idx_candidates_pipeline_stage", "candidates", ["pipeline_stage"])
    _enable_rls("candidates")

    # ─── job_posts — tin tuyển dụng public career page ───
    op.create_table(
        "job_posts",
        *_tenant_columns(),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campaigns.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("organization_id", "slug", name="uq_job_posts_org_slug"),
    )
    op.create_index("idx_job_posts_organization_id", "job_posts", ["organization_id"])
    op.create_index("idx_job_posts_campaign_id", "job_posts", ["campaign_id"])
    _enable_rls("job_posts")


def downgrade() -> None:
    for table in ("job_posts", "candidates", "campaigns"):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.drop_table(table)
