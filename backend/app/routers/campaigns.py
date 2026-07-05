# Campaigns router — CRUD đợt tuyển dụng (Sprint 2-3)
# Mọi query auto-filter tenant + filter explicit (defense in depth)

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_hr_manager
from app.core.responses import paginated, success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import ResourceNotFound
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignResponse, CampaignUpdate

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


async def get_campaign_or_404(campaign_id: UUID, db: AsyncSession) -> Campaign:
    """Lấy campaign trong tenant hiện tại — cross-tenant rơi vào 404 nhờ auto-filter."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise ResourceNotFound("đợt tuyển dụng")
    return campaign


@router.get("")
async def list_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = None,
    status: str | None = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    org_id = get_current_org_id()
    query = select(Campaign).where(Campaign.organization_id == org_id)
    count_query = select(func.count(Campaign.id)).where(Campaign.organization_id == org_id)

    if status:
        query = query.where(Campaign.status == status)
        count_query = count_query.where(Campaign.status == status)
    elif not include_inactive:
        query = query.where(Campaign.status != "inactive")
        count_query = count_query.where(Campaign.status != "inactive")

    if search:
        pattern = f"%{search}%"
        cond = Campaign.name.ilike(pattern) | Campaign.position.ilike(pattern)
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(Campaign.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    items = result.scalars().all()

    return paginated(
        [CampaignResponse.model_validate(c).model_dump(mode="json") for c in items],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    campaign = await get_campaign_or_404(campaign_id, db)
    return success(CampaignResponse.model_validate(campaign).model_dump(mode="json"))


@router.post("", status_code=201)
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    # organization_id KHÔNG lấy từ client — before_flush listener tự gán từ context
    campaign = Campaign(**data.model_dump(), status="draft")
    db.add(campaign)
    await db.flush()
    await db.refresh(campaign)
    return success(
        CampaignResponse.model_validate(campaign).model_dump(mode="json"),
        message="Đã tạo đợt tuyển dụng",
    )


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    campaign = await get_campaign_or_404(campaign_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(campaign, field, value)
    await db.flush()
    await db.refresh(campaign)
    return success(
        CampaignResponse.model_validate(campaign).model_dump(mode="json"),
        message="Đã cập nhật đợt tuyển dụng",
    )


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    # Soft delete — KHÔNG hard delete (rules/soft-delete.md)
    campaign = await get_campaign_or_404(campaign_id, db)
    campaign.status = "inactive"
    return success(None, message="Đã xóa đợt tuyển dụng")
