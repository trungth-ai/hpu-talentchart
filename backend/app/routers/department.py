# Cơ cấu tổ chức — CRUD phòng ban (cây). Đọc: staff (mọi nhân viên); tạo/sửa/xóa: admin.
# Trả list phẳng (có parent_id) — frontend dựng cây. Kèm số nhân sự mỗi phòng.

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_admin, require_staff
from app.core.responses import success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import BusinessRuleError, ResourceNotFound
from app.models.candidate import Candidate
from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter(prefix="/departments", tags=["departments"])


async def _get_or_404(department_id: UUID, db: AsyncSession) -> Department:
    result = await db.execute(select(Department).where(Department.id == department_id))
    dep = result.scalar_one_or_none()
    if dep is None:
        raise ResourceNotFound("phòng ban")  # cross-tenant → 404 nhờ auto-filter
    return dep


async def _verify_manager(manager_user_id: UUID | None, db: AsyncSession) -> None:
    """Trưởng đơn vị phải là user cùng tổ chức (chặn IDOR qua foreign key)."""
    if manager_user_id is not None:
        r = await db.execute(select(User.id).where(User.id == manager_user_id))
        if r.scalar_one_or_none() is None:
            raise ResourceNotFound("người dùng (trưởng đơn vị)")


@router.get("")
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_staff),
):
    org_id = get_current_org_id()
    result = await db.execute(
        select(Department)
        .where(Department.organization_id == org_id)
        .where(Department.status == "active")
        .order_by(Department.name)
    )
    deps = result.scalars().all()
    counts = dict(
        (
            await db.execute(
                select(Candidate.department_id, func.count(Candidate.id))
                .where(Candidate.organization_id == org_id)
                .where(Candidate.status == "active")
                .where(Candidate.department_id.is_not(None))
                .group_by(Candidate.department_id)
            )
        ).all()
    )
    items = []
    for d in deps:
        data = DepartmentResponse.model_validate(d).model_dump(mode="json")
        data["member_count"] = counts.get(d.id, 0)
        items.append(data)
    return success(items)


@router.post("", status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if data.parent_id is not None:
        await _get_or_404(data.parent_id, db)  # cha phải cùng tenant
    await _verify_manager(data.manager_user_id, db)
    dep = Department(
        name=data.name, parent_id=data.parent_id, manager_user_id=data.manager_user_id
    )
    db.add(dep)
    await db.flush()
    await db.refresh(dep)
    return success(
        DepartmentResponse.model_validate(dep).model_dump(mode="json"),
        message="Đã tạo phòng ban",
    )


@router.put("/{department_id}")
async def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    dep = await _get_or_404(department_id, db)
    payload = data.model_dump(exclude_unset=True)
    if payload.get("parent_id"):
        if payload["parent_id"] == department_id:
            raise BusinessRuleError("Phòng ban không thể là cha của chính nó")
        await _get_or_404(payload["parent_id"], db)
    if "manager_user_id" in payload:
        await _verify_manager(payload["manager_user_id"], db)
    for field, value in payload.items():
        setattr(dep, field, value)
    await db.flush()
    await db.refresh(dep)
    return success(
        DepartmentResponse.model_validate(dep).model_dump(mode="json"),
        message="Đã cập nhật phòng ban",
    )


@router.delete("/{department_id}")
async def delete_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    dep = await _get_or_404(department_id, db)
    children = await db.execute(
        select(func.count(Department.id))
        .where(Department.parent_id == department_id)
        .where(Department.status == "active")
    )
    if children.scalar_one() > 0:
        raise BusinessRuleError("Không thể xóa: còn phòng ban con — hãy chuyển/xóa phòng con trước")
    # Gỡ nhân sự khỏi phòng bị xóa (tránh trỏ tới phòng đã ẩn)
    rows = await db.execute(select(Candidate).where(Candidate.department_id == department_id))
    for c in rows.scalars().all():
        c.department_id = None
    dep.status = "inactive"  # soft delete (không hard delete — rules/soft-delete.md)
    return success(None, message="Đã xóa phòng ban")
