# Test links router — HR gửi bài test DISC cho ứng viên (port flow từ SmartHire)
# Gắn với pipeline: tạo link khi RECEIVED (tự chuyển ASSESSMENT) hoặc ASSESSMENT (gửi lại).
# Nộp bài KHÔNG đổi trạng thái (đã gộp — ADR-008); "đã làm" tra theo TestSession.completed_at.

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.permissions import require_hr_manager
from app.core.responses import paginated, success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import BusinessRuleError, ResourceNotFound
from app.models.candidate import Candidate
from app.models.organization import Organization
from app.models.test_session import TestSession
from app.models.user import User
from app.schemas.test_session import AdminTestResult, TestLinkCreate, TestLinkResponse
from app.services import candidate_service

router = APIRouter(prefix="/test-links", tags=["test-links"])

settings = get_settings()


async def _build_test_url(db: AsyncSession, token: str) -> str:
    """URL làm bài theo subdomain tenant: https://{slug}.talentchart.hpu.edu.vn/test/{token}"""
    org_id = get_current_org_id()
    result = await db.execute(select(Organization.slug).where(Organization.id == org_id))
    slug = result.scalar_one_or_none() or "app"
    scheme = "http" if settings.is_development else "https"
    return f"{scheme}://{slug}.{settings.BASE_DOMAIN}/test/{token}"


@router.post("", status_code=201)
async def create_test_link(
    data: TestLinkCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    result = await db.execute(select(Candidate).where(Candidate.id == data.candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise ResourceNotFound("ứng viên")

    # Gửi test khi đang RECEIVED (tự chuyển ASSESSMENT) hoặc đã ASSESSMENT (gửi lại link —
    # link cũ chưa dùng sẽ bị vô hiệu)
    if candidate.pipeline_stage == "RECEIVED":
        candidate_service.transition_pipeline(candidate, "ASSESSMENT")
    elif candidate.pipeline_stage != "ASSESSMENT":
        raise BusinessRuleError(
            f"Chỉ gửi được bài test khi ứng viên ở bước Tiếp nhận hoặc Đánh giá "
            f"(hiện tại: {candidate.pipeline_stage})"
        )

    # Vô hiệu link cũ chưa dùng của ứng viên này (soft — đánh dấu inactive)
    old_links = await db.execute(
        select(TestSession)
        .where(TestSession.candidate_id == candidate.id)
        .where(TestSession.is_used.is_(False))
        .where(TestSession.status == "active")
    )
    for old in old_links.scalars().all():
        old.status = "inactive"

    session = TestSession(
        candidate_id=candidate.id,
        token=secrets.token_urlsafe(48),
        expires_at=datetime.now(UTC) + timedelta(hours=data.expires_hours),
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    response = TestLinkResponse(
        id=session.id,
        candidate_id=session.candidate_id,
        token=session.token,
        test_url=await _build_test_url(db, session.token),
        expires_at=session.expires_at,
        is_used=session.is_used,
        completed_at=session.completed_at,
        created_at=session.created_at,
    )
    return success(response.model_dump(mode="json"), message="Đã tạo link bài test")


@router.get("")
async def list_test_links(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    candidate_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    org_id = get_current_org_id()
    query = (
        select(TestSession)
        .where(TestSession.organization_id == org_id)
        .where(TestSession.status == "active")
    )
    count_query = (
        select(func.count(TestSession.id))
        .where(TestSession.organization_id == org_id)
        .where(TestSession.status == "active")
    )
    if candidate_id:
        query = query.where(TestSession.candidate_id == candidate_id)
        count_query = count_query.where(TestSession.candidate_id == candidate_id)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(TestSession.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        items.append(
            TestLinkResponse(
                id=s.id,
                candidate_id=s.candidate_id,
                token=s.token,
                test_url=await _build_test_url(db, s.token),
                expires_at=s.expires_at,
                is_used=s.is_used,
                completed_at=s.completed_at,
                created_at=s.created_at,
            ).model_dump(mode="json")
        )
    return paginated(items, page=page, per_page=per_page, total=total)


@router.get("/candidates/{candidate_id}/result")
async def get_candidate_test_result(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Kết quả test đầy đủ của ứng viên (bản HR — kèm phân tích + gợi ý phỏng vấn)."""
    # Xác nhận candidate thuộc tenant (cross-tenant → 404)
    cand = await db.execute(select(Candidate.id).where(Candidate.id == candidate_id))
    if cand.scalar_one_or_none() is None:
        raise ResourceNotFound("ứng viên")

    result = await db.execute(
        select(TestSession)
        .where(TestSession.candidate_id == candidate_id)
        .where(TestSession.completed_at.isnot(None))
        .order_by(TestSession.completed_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ResourceNotFound("kết quả bài test")

    return success(
        AdminTestResult(
            disc_scores=session.disc_scores,
            disc_primary=session.disc_primary,
            disc_secondary=session.disc_secondary,
            disc_profile=session.disc_profile,
            personality_scores=session.personality_scores,
            analysis=session.analysis,
            ai_suggestions=session.ai_suggestions,
            overall_score=session.overall_score,
            recommendation=session.recommendation,
            completed_at=session.completed_at,
        ).model_dump(mode="json")
    )
