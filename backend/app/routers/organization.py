# Organization router — xem thông tin tổ chức + cập nhật cài đặt (Eastern Layer, Google Workspace).
# Admin chỉ sửa tổ chức của mình (org_id lấy từ tenant context, không nhận từ client).

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin, require_hr_manager
from app.core.responses import success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import ResourceNotFound
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationResponse, OrgSettingsUpdate

router = APIRouter(prefix="/organization", tags=["organization"])


async def _current_org(db: AsyncSession) -> Organization:
    org_id = get_current_org_id()
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if org is None:
        raise ResourceNotFound("tổ chức")
    return org


@router.get("")
async def get_organization(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Thông tin tổ chức hiện tại + settings (để hiển thị trang Cài đặt tổ chức)."""
    org = await _current_org(db)
    return success(OrganizationResponse.model_validate(org).model_dump(mode="json"))


@router.put("/settings")
async def update_org_settings(
    data: OrgSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Cập nhật cài đặt tổ chức — CHỈ owner/admin."""
    org = await _current_org(db)
    # Gộp vào settings hiện có; gán dict MỚI để SQLAlchemy nhận diện thay đổi cột JSON
    new_settings = dict(org.settings or {})
    new_settings.update(data.model_dump(exclude_unset=True))
    org.settings = new_settings
    await db.flush()
    await db.refresh(org)
    return success(
        OrganizationResponse.model_validate(org).model_dump(mode="json"),
        message="Đã cập nhật cài đặt tổ chức",
    )
