# ★ Database — async engine + session + tenant filter tự động (ADR-003, lớp bảo vệ số 2)
#
# 3 lớp bảo vệ tenant isolation:
#   1. TenantMiddleware set tenant context (middleware/tenant.py)
#   2. Event listener ở file này tự inject filter organization_id vào MỌI query ORM
#   3. PostgreSQL RLS (policy trong Alembic migration) — safety-net cuối cùng

from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, with_loader_criteria
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.core.tenant_context import get_current_org_id
from app.models.base import TenantScopedBase

settings = get_settings()

# SQLite in-memory (chỉ dùng cho test) cần StaticPool để mọi session chung 1 connection
_engine_kwargs: dict = {"echo": False}
if settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["poolclass"] = StaticPool
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_filter(execute_state) -> None:
    """★ Lớp bảo vệ số 2: tự động thêm WHERE organization_id = ... vào mọi query ORM.

    Áp dụng cho SELECT/UPDATE/DELETE trên mọi model kế thừa TenantScopedBase.
    Nếu chưa có tenant context (VD: /health, script hệ thống) thì không filter —
    khi đó RLS ở tầng PostgreSQL vẫn chặn (lớp số 3).
    """
    org_id = get_current_org_id()
    if org_id is None:
        return
    if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                TenantScopedBase,
                lambda cls: cls.organization_id == org_id,
                include_aliases=True,
            )
        )


@event.listens_for(Session, "before_flush")
def _guard_tenant_writes(session: Session, flush_context, instances) -> None:
    """Chặn ghi dữ liệu sai tenant ngay tại ORM:

    - Object mới thiếu organization_id → tự set từ tenant context
      (organization_id KHÔNG BAO GIỜ lấy từ client — rule tenant-isolation số 5)
    - Object có organization_id khác tenant hiện tại → raise ngay, không cho flush
    """
    org_id = get_current_org_id()
    if org_id is None:
        return
    for obj in session.new:
        if isinstance(obj, TenantScopedBase):
            if obj.organization_id is None:
                obj.organization_id = org_id
            elif obj.organization_id != org_id:
                raise PermissionError(
                    "Phát hiện ghi dữ liệu sai tenant — organization_id không khớp context"
                )
    for obj in session.dirty:
        if isinstance(obj, TenantScopedBase) and obj.organization_id != org_id:
            raise PermissionError(
                "Phát hiện sửa dữ liệu của tenant khác — từ chối flush"
            )


async def set_rls_guc(session: AsyncSession) -> None:
    """Lớp bảo vệ số 3: set biến app.current_org_id cho PostgreSQL RLS policy.

    SET LOCAL — chỉ có hiệu lực trong transaction hiện tại của session này.
    Chỉ chạy trên PostgreSQL (test dùng SQLite sẽ bỏ qua).
    """
    org_id = get_current_org_id()
    if org_id is not None and engine.dialect.name == "postgresql":
        await session.execute(
            text("SELECT set_config('app.current_org_id', :org_id, true)"),
            {"org_id": str(org_id)},
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency cấp session cho router — đã gắn đủ 3 lớp bảo vệ tenant."""
    async with async_session_factory() as session:
        await set_rls_guc(session)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
