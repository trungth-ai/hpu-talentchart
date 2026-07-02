# RBAC — OrgRole + dependency lấy user hiện tại và kiểm tra quyền
# Lưu ý: thiếu quyền hệ thống → 403; cross-tenant → LUÔN 404 (đã xử lý bằng tenant filter)

from enum import StrEnum
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User


class OrgRole(StrEnum):
    """Vai trò trong tổ chức — thứ tự từ cao xuống thấp."""

    OWNER = "owner"
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    MEMBER = "member"


# Cấp bậc để so sánh quyền (số lớn = quyền cao)
ROLE_LEVEL: dict[str, int] = {
    OrgRole.OWNER: 50,
    OrgRole.ADMIN: 40,
    OrgRole.HR_MANAGER: 30,
    OrgRole.RECRUITER: 20,
    OrgRole.MEMBER: 10,
}


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency: lấy user từ JWT (AuthMiddleware đã decode vào request.state).

    Query User tự động được filter theo tenant context — nếu token thuộc org khác
    với tenant đang resolve thì không tìm thấy user → 401.
    """
    payload = getattr(request.state, "token_payload", None)
    if payload is None:
        raise UnauthorizedError()

    user_id = payload.get("sub")
    org_id = get_current_org_id()
    if user_id is None or org_id is None:
        raise UnauthorizedError()

    # Filter explicit organization_id dù đã có auto-filter (defense in depth)
    result = await db.execute(
        select(User)
        .where(User.id == UUID(user_id))
        .where(User.organization_id == org_id)
        .where(User.status == "active")
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError()
    return user


def require_org_role(minimum_role: OrgRole):
    """Dependency factory: yêu cầu org_role tối thiểu. Thiếu quyền → 403 FORBIDDEN."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if ROLE_LEVEL.get(user.org_role, 0) < ROLE_LEVEL[minimum_role]:
            raise ForbiddenError()
        return user

    return _checker


# Singleton dependencies dùng chung cho router (tránh gọi factory trong default argument)
require_hr_manager = require_org_role(OrgRole.HR_MANAGER)
require_admin = require_org_role(OrgRole.ADMIN)
