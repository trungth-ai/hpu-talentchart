# Public test API — ứng viên làm bài DISC qua link token (không cần đăng nhập)
# Tenant resolve theo subdomain. Nộp bài → chấm điểm (DISC engine port) → TEST_DONE.

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import BusinessRuleError, ResourceNotFound
from app.middleware.rate_limit import limiter
from app.models.candidate import Candidate
from app.models.test_session import TestSession
from app.schemas.test_session import PublicTestResult, TestSubmission
from app.services import candidate_service, disc_service

router = APIRouter(prefix="/public/test", tags=["public"])

SUBMIT_RATE_LIMIT = "10/minute"


def _as_utc(value: datetime) -> datetime:
    """SQLite không lưu tzinfo — datetime naive từ DB coi như UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


async def _get_valid_session(token: str, db: AsyncSession) -> TestSession:
    """Validate token trong tenant hiện tại — sai tenant/không tồn tại → 404."""
    if get_current_org_id() is None:
        raise ResourceNotFound("bài test")

    result = await db.execute(
        select(TestSession)
        .where(TestSession.token == token)
        .where(TestSession.status == "active")
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ResourceNotFound("bài test")
    if session.is_used:
        raise BusinessRuleError("Bài test này đã được nộp rồi")
    if _as_utc(session.expires_at) < datetime.now(UTC):
        raise BusinessRuleError("Link bài test đã hết hạn — liên hệ phòng nhân sự để gửi lại")
    return session


@router.get("/{token}")
async def get_test(token: str, db: AsyncSession = Depends(get_db)):
    """Thông tin bài test + bộ câu hỏi (KHÔNG kèm đáp án mapping)."""
    session = await _get_valid_session(token, db)

    result = await db.execute(select(Candidate).where(Candidate.id == session.candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise ResourceNotFound("bài test")

    return success(
        {
            "candidate_name": candidate.full_name,
            "position": candidate.position,
            "expires_at": session.expires_at.isoformat(),
            **disc_service.get_public_questions(),
        }
    )


@router.post("/{token}/submit")
@limiter.limit(SUBMIT_RATE_LIMIT)
async def submit_test(
    request: Request,
    token: str,
    data: TestSubmission,
    db: AsyncSession = Depends(get_db),
):
    """Nộp bài — chấm điểm bằng DISC engine (port nguyên xi từ SmartHire)."""
    session = await _get_valid_session(token, db)

    result = await db.execute(select(Candidate).where(Candidate.id == session.candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise ResourceNotFound("bài test")

    # Chấm điểm — logic port từ SmartHire, đã có test parity
    disc_result = disc_service.calculate_disc(data.disc_answers)
    personality_scores = disc_service.calculate_personality(data.personality_answers)
    analysis = disc_service.generate_analysis(
        disc_result, personality_scores, candidate.position or ""
    )
    ai_suggestions = disc_service.generate_ai_interview_suggestions(
        disc_result, personality_scores, candidate.position or ""
    )

    now = datetime.now(UTC)
    session.disc_answers = data.disc_answers
    session.personality_answers = data.personality_answers
    session.disc_scores = disc_result["disc_scores"]
    session.disc_primary = disc_result["disc_primary"]
    session.disc_secondary = disc_result["disc_secondary"]
    session.disc_profile = disc_result["disc_profile"]
    session.personality_scores = personality_scores
    session.analysis = analysis
    session.ai_suggestions = ai_suggestions
    session.overall_score = analysis["overall_score"]
    session.recommendation = analysis["recommendation"]
    session.is_used = True
    session.completed_at = now

    # Pipeline tuần tự: TEST_SENT → TEST_DONE
    if candidate.pipeline_stage == "TEST_SENT":
        candidate_service.transition_pipeline(candidate, "TEST_DONE")

    # Ứng viên chỉ nhận Behavioural Layer — không nhận phân tích/khuyến nghị nội bộ
    return success(
        PublicTestResult(
            disc_scores=disc_result["disc_scores"],
            disc_primary=disc_result["disc_primary"],
            disc_secondary=disc_result["disc_secondary"],
            disc_profile=disc_result["disc_profile"],
            personality_scores=personality_scores,
        ).model_dump(mode="json"),
        message="Đã nộp bài test thành công. Cảm ơn bạn!",
    )
