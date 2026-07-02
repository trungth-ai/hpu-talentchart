# Tenant context — lưu organization_id của request hiện tại bằng contextvars
# Được TenantMiddleware set ở đầu request và reset ở cuối request.
# database.py đọc context này để tự động filter mọi query (lớp bảo vệ số 2 theo ADR-003).

from contextvars import ContextVar, Token
from uuid import UUID

# None = chưa xác định tenant (VD: /health, /docs, super-admin platform)
_current_org_id: ContextVar[UUID | None] = ContextVar("current_org_id", default=None)


def get_current_org_id() -> UUID | None:
    """Lấy organization_id của request hiện tại (None nếu ngoài tenant context)."""
    return _current_org_id.get()


def set_current_org_id(org_id: UUID | None) -> Token:
    """Set tenant context, trả về token để reset sau khi request kết thúc."""
    return _current_org_id.set(org_id)


def reset_current_org_id(token: Token) -> None:
    """Reset tenant context về trạng thái trước đó (gọi trong finally của middleware)."""
    _current_org_id.reset(token)
