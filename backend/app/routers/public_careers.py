# Public Career Page API — KHÔNG cần đăng nhập (Sprint 4)
# Tenant resolve qua subdomain: {org-slug}.talentchart.hpu.edu.vn (TenantMiddleware)
# Chỉ hiện tin đã publish; đơn ứng tuyển tạo Candidate ở trạng thái NEW.

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import BusinessRuleError, ResourceNotFound
from app.middleware.rate_limit import limiter
from app.models.candidate import Candidate
from app.models.job_post import JobPost
from app.schemas.job_post import PublicApplication, PublicJobResponse

router = APIRouter(prefix="/public", tags=["public"])

# Chống spam form ứng tuyển từ career page công khai
APPLY_RATE_LIMIT = "10/minute"


def _require_tenant() -> UUID:
    """Public API bắt buộc có tenant (subdomain) — không có → 404 (không leak gì thêm)."""
    org_id = get_current_org_id()
    if org_id is None:
        raise ResourceNotFound("trang tuyển dụng")
    return org_id


def _published_jobs_query(org_id: UUID):
    return (
        select(JobPost)
        .where(JobPost.organization_id == org_id)
        .where(JobPost.status == "active")
        .where(JobPost.is_published.is_(True))
    )


@router.get("/jobs")
async def list_public_jobs(db: AsyncSession = Depends(get_db)):
    org_id = _require_tenant()
    result = await db.execute(
        _published_jobs_query(org_id).order_by(JobPost.published_at.desc())
    )
    jobs = result.scalars().all()
    return success(
        [PublicJobResponse.model_validate(j).model_dump(mode="json") for j in jobs]
    )


@router.get("/jobs/{slug}")
async def get_public_job(slug: str, db: AsyncSession = Depends(get_db)):
    org_id = _require_tenant()
    result = await db.execute(_published_jobs_query(org_id).where(JobPost.slug == slug))
    job = result.scalar_one_or_none()
    if job is None:
        raise ResourceNotFound("tin tuyển dụng")
    return success(PublicJobResponse.model_validate(job).model_dump(mode="json"))


@router.post("/jobs/{slug}/apply", status_code=201)
@limiter.limit(APPLY_RATE_LIMIT)
async def apply_to_job(
    request: Request,
    slug: str,
    data: PublicApplication,
    db: AsyncSession = Depends(get_db),
):
    org_id = _require_tenant()
    result = await db.execute(_published_jobs_query(org_id).where(JobPost.slug == slug))
    job = result.scalar_one_or_none()
    if job is None:
        raise ResourceNotFound("tin tuyển dụng")

    # Chặn ứng tuyển trùng: cùng email + cùng tin còn đang xử lý
    existing = await db.execute(
        select(Candidate.id)
        .where(Candidate.organization_id == org_id)
        .where(Candidate.email == data.email.lower())
        .where(Candidate.campaign_id == job.campaign_id)
        .where(Candidate.status == "active")
        .where(Candidate.position == job.title)
    )
    if existing.scalar_one_or_none():
        raise BusinessRuleError("Bạn đã ứng tuyển vị trí này rồi")

    candidate = Candidate(
        full_name=data.full_name,
        email=data.email.lower(),
        phone=data.phone,
        notes=data.notes,
        candidate_type="applicant",
        pipeline_stage="NEW",
        position=job.title,
        source="career_page",
        campaign_id=job.campaign_id,
        epa_consent=data.epa_consent,
        epa_consent_at=datetime.now(UTC) if data.epa_consent else None,
        birth_date=data.birth_date,
        birth_time=data.birth_time,
        birth_place=data.birth_place,
        # organization_id tự gán từ tenant context (before_flush listener)
    )
    db.add(candidate)
    await db.flush()

    return success(
        {"application_id": str(candidate.id)},
        message="Đã nhận hồ sơ ứng tuyển của bạn. Chúng tôi sẽ liên hệ sớm!",
    )
