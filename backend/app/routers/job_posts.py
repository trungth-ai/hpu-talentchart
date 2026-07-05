# JobPosts router — admin CRUD tin tuyển dụng (Sprint 4)
# Public career page ở router riêng: routers/public_careers.py

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_hr_manager
from app.core.responses import paginated, success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import DuplicateResource, ResourceNotFound
from app.models.job_post import JobPost
from app.models.user import User
from app.routers.campaigns import get_campaign_or_404
from app.schemas.job_post import JobPostCreate, JobPostResponse, JobPostUpdate

router = APIRouter(prefix="/job-posts", tags=["job-posts"])


async def _get_job_post_or_404(job_post_id: UUID, db: AsyncSession) -> JobPost:
    result = await db.execute(select(JobPost).where(JobPost.id == job_post_id))
    job_post = result.scalar_one_or_none()
    if job_post is None:
        raise ResourceNotFound("tin tuyển dụng")
    return job_post


async def _verify_slug_unique(slug: str, db: AsyncSession, exclude_id: UUID | None = None) -> None:
    """Slug unique trong org — báo 409 sớm thay vì lỗi constraint khó hiểu."""
    org_id = get_current_org_id()
    query = (
        select(JobPost.id)
        .where(JobPost.organization_id == org_id)
        .where(JobPost.slug == slug)
    )
    if exclude_id:
        query = query.where(JobPost.id != exclude_id)
    if (await db.execute(query)).scalar_one_or_none():
        raise DuplicateResource(f"Slug '{slug}' đã được dùng cho tin tuyển dụng khác")


@router.get("")
async def list_job_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = None,
    is_published: bool | None = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    org_id = get_current_org_id()
    query = select(JobPost).where(JobPost.organization_id == org_id)
    count_query = select(func.count(JobPost.id)).where(JobPost.organization_id == org_id)

    if not include_inactive:
        query = query.where(JobPost.status == "active")
        count_query = count_query.where(JobPost.status == "active")
    if is_published is not None:
        query = query.where(JobPost.is_published == is_published)
        count_query = count_query.where(JobPost.is_published == is_published)
    if search:
        pattern = f"%{search}%"
        query = query.where(JobPost.title.ilike(pattern))
        count_query = count_query.where(JobPost.title.ilike(pattern))

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(JobPost.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()

    return paginated(
        [JobPostResponse.model_validate(j).model_dump(mode="json") for j in items],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{job_post_id}")
async def get_job_post(
    job_post_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    job_post = await _get_job_post_or_404(job_post_id, db)
    return success(JobPostResponse.model_validate(job_post).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_job_post(
    data: JobPostCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    if data.campaign_id:
        # Chặn gán campaign của tenant khác (cross-tenant → 404)
        await get_campaign_or_404(data.campaign_id, db)
    await _verify_slug_unique(data.slug, db)

    job_post = JobPost(**data.model_dump())
    db.add(job_post)
    await db.flush()
    await db.refresh(job_post)
    return success(
        JobPostResponse.model_validate(job_post).model_dump(mode="json"),
        message="Đã tạo tin tuyển dụng",
    )


@router.put("/{job_post_id}")
async def update_job_post(
    job_post_id: UUID,
    data: JobPostUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    job_post = await _get_job_post_or_404(job_post_id, db)
    payload = data.model_dump(exclude_unset=True)
    if payload.get("campaign_id"):
        await get_campaign_or_404(payload["campaign_id"], db)
    if "slug" in payload and payload["slug"]:
        await _verify_slug_unique(payload["slug"], db, exclude_id=job_post.id)

    for field, value in payload.items():
        setattr(job_post, field, value)
    await db.flush()
    await db.refresh(job_post)
    return success(
        JobPostResponse.model_validate(job_post).model_dump(mode="json"),
        message="Đã cập nhật tin tuyển dụng",
    )


@router.post("/{job_post_id}/publish")
async def publish_job_post(
    job_post_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    job_post = await _get_job_post_or_404(job_post_id, db)
    job_post.is_published = True
    job_post.published_at = datetime.now(UTC)
    return success(None, message="Đã đăng tin tuyển dụng lên Career Page")


@router.post("/{job_post_id}/unpublish")
async def unpublish_job_post(
    job_post_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    job_post = await _get_job_post_or_404(job_post_id, db)
    job_post.is_published = False
    return success(None, message="Đã gỡ tin tuyển dụng khỏi Career Page")


@router.delete("/{job_post_id}")
async def delete_job_post(
    job_post_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    # Soft delete + gỡ khỏi career page
    job_post = await _get_job_post_or_404(job_post_id, db)
    job_post.status = "inactive"
    job_post.is_published = False
    return success(None, message="Đã xóa tin tuyển dụng")
