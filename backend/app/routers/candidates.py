# Candidates router — ATS Core (Sprint 2-3)
# Pipeline chỉ đổi qua POST /{id}/transition (state machine trong candidate_service)

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_hr_manager
from app.core.responses import paginated, success
from app.core.tenant_context import get_current_org_id
from app.data.horoscope import get_sign_by_date
from app.database import get_db
from app.exceptions import ResourceNotFound
from app.models.candidate import PIPELINE_STAGES, Candidate
from app.models.user import User
from app.routers.campaigns import get_campaign_or_404
from app.schemas.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateUpdate,
    PipelineTransition,
)
from app.services import candidate_service
from app.services.epa import canchi

router = APIRouter(prefix="/candidates", tags=["candidates"])


async def _get_candidate_or_404(candidate_id: UUID, db: AsyncSession) -> Candidate:
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise ResourceNotFound("ứng viên")
    return candidate


async def _verify_campaign_same_tenant(campaign_id: UUID | None, db: AsyncSession) -> None:
    """Chặn gán candidate vào campaign của tenant khác (IDOR qua foreign key).

    Lookup qua auto-filter: campaign org khác → không thấy → 404 (không leak existence).
    """
    if campaign_id is not None:
        await get_campaign_or_404(campaign_id, db)


def _serialize_candidate(c: Candidate) -> dict:
    """CandidateResponse + bổ sung Can Chi/cung/năm sinh (khi đã opt-in EPA + có ngày sinh)
    để hiển thị cột ở màn danh sách. KHÔNG lộ ngày/giờ/nơi sinh chi tiết."""
    data = CandidateResponse.model_validate(c).model_dump(mode="json")
    if c.epa_consent and c.birth_date:
        z = canchi.get_canchi_from_birth(c.birth_date.day, c.birth_date.month, c.birth_date.year)
        data["birth_year"] = c.birth_date.year
        data["tuoi_am"] = z["tuoi_am"]
        data["con_giap"] = z["con_giap"]
        data["menh"] = z["menh"]
        data["cung_hoang_dao"] = get_sign_by_date(c.birth_date)["name"]
    return data


@router.get("")
async def list_candidates(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = None,
    pipeline_stage: str | None = None,
    candidate_type: str | None = None,
    campaign_id: UUID | None = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    org_id = get_current_org_id()
    query = select(Candidate).where(Candidate.organization_id == org_id)
    count_query = select(func.count(Candidate.id)).where(Candidate.organization_id == org_id)

    if not include_inactive:
        query = query.where(Candidate.status == "active")
        count_query = count_query.where(Candidate.status == "active")
    if pipeline_stage:
        query = query.where(Candidate.pipeline_stage == pipeline_stage)
        count_query = count_query.where(Candidate.pipeline_stage == pipeline_stage)
    if candidate_type:
        query = query.where(Candidate.candidate_type == candidate_type)
        count_query = count_query.where(Candidate.candidate_type == candidate_type)
    if campaign_id:
        query = query.where(Candidate.campaign_id == campaign_id)
        count_query = count_query.where(Candidate.campaign_id == campaign_id)
    if search:
        pattern = f"%{search}%"
        cond = Candidate.full_name.ilike(pattern) | Candidate.email.ilike(pattern)
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Candidate.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()

    return paginated(
        [_serialize_candidate(c) for c in items],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/stats")
async def candidate_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Thống kê số ứng viên theo từng trạng thái pipeline (cho dashboard)."""
    org_id = get_current_org_id()
    result = await db.execute(
        select(Candidate.pipeline_stage, func.count(Candidate.id))
        .where(Candidate.organization_id == org_id)
        .where(Candidate.status == "active")
        .group_by(Candidate.pipeline_stage)
    )
    counts = dict(result.all())
    return success({stage: counts.get(stage, 0) for stage in PIPELINE_STAGES})


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    candidate = await _get_candidate_or_404(candidate_id, db)
    return success(CandidateResponse.model_validate(candidate).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_candidate(
    data: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    await _verify_campaign_same_tenant(data.campaign_id, db)

    payload = data.model_dump()
    if payload.pop("epa_consent"):
        payload["epa_consent"] = True
        payload["epa_consent_at"] = datetime.now(UTC)

    email = payload.pop("email").lower()
    candidate = Candidate(**payload, email=email)
    db.add(candidate)
    await db.flush()
    await db.refresh(candidate)
    return success(
        CandidateResponse.model_validate(candidate).model_dump(mode="json"),
        message="Đã tạo ứng viên",
    )


@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: UUID,
    data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    candidate = await _get_candidate_or_404(candidate_id, db)

    payload = data.model_dump(exclude_unset=True)
    if "campaign_id" in payload:
        await _verify_campaign_same_tenant(payload["campaign_id"], db)
    if "email" in payload and payload["email"]:
        payload["email"] = payload["email"].lower()
    if payload.get("epa_consent") is True and not candidate.epa_consent:
        payload["epa_consent_at"] = datetime.now(UTC)
    if payload.get("epa_consent") is False:
        # Rút consent = xóa luôn dữ liệu nhạy cảm (NĐ 13/2023)
        candidate_service.clear_epa_data(candidate)
        payload.pop("epa_consent")

    for field, value in payload.items():
        setattr(candidate, field, value)
    await db.flush()
    await db.refresh(candidate)
    return success(
        CandidateResponse.model_validate(candidate).model_dump(mode="json"),
        message="Đã cập nhật ứng viên",
    )


@router.post("/{candidate_id}/transition")
async def transition_candidate(
    candidate_id: UUID,
    data: PipelineTransition,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Chuyển trạng thái pipeline — CHỈ tuần tự, vi phạm trả 422 BUSINESS_RULE_ERROR."""
    candidate = await _get_candidate_or_404(candidate_id, db)
    candidate_service.transition_pipeline(candidate, data.target_stage)
    await db.flush()
    await db.refresh(candidate)
    return success(
        CandidateResponse.model_validate(candidate).model_dump(mode="json"),
        message=f"Đã chuyển sang {candidate.pipeline_stage}",
    )


@router.delete("/{candidate_id}/epa-data")
async def delete_epa_data(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Xóa dữ liệu nhạy cảm EPA theo yêu cầu ứng viên (NĐ 13/2023 — quyền xóa 30 ngày)."""
    candidate = await _get_candidate_or_404(candidate_id, db)
    candidate_service.clear_epa_data(candidate)
    return success(None, message="Đã xóa dữ liệu sinh trắc EPA của ứng viên")


@router.delete("/{candidate_id}")
async def delete_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    # Soft delete
    candidate = await _get_candidate_or_404(candidate_id, db)
    candidate.status = "inactive"
    return success(None, message="Đã xóa ứng viên")
