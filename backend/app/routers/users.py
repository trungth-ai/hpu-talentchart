# Users router — list/get user trong tổ chức (mục tiêu chính của test_tenant_isolation.py)
# Cross-tenant access LUÔN trả 404 (rule tenant-isolation số 3)

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ROLE_LEVEL, require_admin, require_hr_manager
from app.core.responses import paginated, success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import BusinessRuleError, ForbiddenError, ResourceNotFound
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: str | None = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    # Auto-filter qua event listener + filter explicit (defense in depth — rule số 2).
    # Lưu ý: query column-only như func.count KHÔNG được with_loader_criteria áp dụng,
    # nên filter explicit ở đây là BẮT BUỘC.
    org_id = get_current_org_id()
    query = select(User).where(User.organization_id == org_id)
    count_query = select(func.count(User.id)).where(User.organization_id == org_id)

    if not include_inactive:
        # Soft delete: mặc định chỉ trả active (rules/soft-delete.md)
        query = query.where(User.status == "active")
        count_query = count_query.where(User.status == "active")

    if search:
        pattern = f"%{search}%"
        cond = User.full_name.ilike(pattern) | User.email.ilike(pattern)
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar_one()
    result = await db.execute(
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    users = result.scalars().all()

    return paginated(
        [UserResponse.model_validate(u).model_dump(mode="json") for u in users],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.get("/{user_id}")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        # User của tenant khác cũng rơi vào nhánh này nhờ auto-filter → 404, KHÔNG 403
        raise ResourceNotFound("người dùng")
    return success(UserResponse.model_validate(user).model_dump(mode="json"))


@router.patch("/{user_id}")
async def update_user_admin(
    user_id: UUID,
    data: UserAdminUpdate,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
):
    """Đổi vai trò / khóa-mở người dùng — CHỈ owner/admin.

    Chốt an toàn (chống leo thang quyền + tự khóa):
    - KHÔNG tự sửa vai trò/khóa chính mình.
    - KHÔNG thao tác trên người có quyền NGANG hoặc CAO hơn mình (chặn admin đụng owner/admin
      khác, và owner đụng owner khác → không thể hạ/khóa owner cuối).
    - KHÔNG cấp vai trò NGANG hoặc CAO hơn quyền của mình (không tự nâng cấp bắc cầu).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise ResourceNotFound("người dùng")  # cross-tenant → 404 nhờ auto-filter
    if target.id == actor.id:
        raise BusinessRuleError("Không thể tự đổi vai trò hoặc tự khóa tài khoản của mình")

    actor_level = ROLE_LEVEL.get(actor.org_role, 0)
    if ROLE_LEVEL.get(target.org_role, 0) >= actor_level:
        raise ForbiddenError("Không thể thao tác trên người có quyền ngang hoặc cao hơn bạn")
    if data.org_role is not None and ROLE_LEVEL[data.org_role] >= actor_level:
        raise ForbiddenError("Không thể cấp vai trò ngang hoặc cao hơn quyền của bạn")

    if data.org_role is not None:
        target.org_role = data.org_role
    if data.status is not None:
        target.status = data.status
    await db.flush()
    await db.refresh(target)
    return success(
        UserResponse.model_validate(target).model_dump(mode="json"),
        message="Đã cập nhật người dùng",
    )
