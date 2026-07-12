# Migration: gộp pipeline 8→5 trạng thái (ADR-008) — remap dữ liệu hồ sơ hiện có.
# pipeline_stage là String validate ở tầng app (không phải enum DB) nên chỉ cần UPDATE dữ liệu.
# Revision 0009.

from collections.abc import Sequence

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NEW + SCREENING       -> RECEIVED (Tiếp nhận)
    # TEST_SENT + TEST_DONE -> ASSESSMENT (Đánh giá)
    # DECISION              -> INTERVIEW (Phỏng vấn); INTERVIEW/HIRED/REJECTED giữ nguyên
    op.execute(
        "UPDATE candidates SET pipeline_stage = 'RECEIVED' "
        "WHERE pipeline_stage IN ('NEW', 'SCREENING')"
    )
    op.execute(
        "UPDATE candidates SET pipeline_stage = 'ASSESSMENT' "
        "WHERE pipeline_stage IN ('TEST_SENT', 'TEST_DONE')"
    )
    op.execute(
        "UPDATE candidates SET pipeline_stage = 'INTERVIEW' WHERE pipeline_stage = 'DECISION'"
    )


def downgrade() -> None:
    # Không khôi phục hoàn hảo được (gộp mất thông tin) — ánh xạ ngược về 1 đại diện hợp lý.
    op.execute(
        "UPDATE candidates SET pipeline_stage = 'SCREENING' WHERE pipeline_stage = 'RECEIVED'"
    )
    op.execute(
        "UPDATE candidates SET pipeline_stage = 'TEST_SENT' WHERE pipeline_stage = 'ASSESSMENT'"
    )
    # INTERVIEW giữ nguyên (không tách lại được INTERVIEW vs DECISION)
