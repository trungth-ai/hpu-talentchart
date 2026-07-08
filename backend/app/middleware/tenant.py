# ★ TenantMiddleware — lớp bảo vệ số 1 (CRITICAL, xem ADR-003)
#
# Resolve organization_id theo thứ tự ưu tiên (PLAN.md, ADR-003, ADR-006):
#   1. JWT claim `organization_id` (AuthMiddleware đã decode trước đó)
#   2. Subdomain: {org-slug}.{BASE_DOMAIN}  (VD: hpu.hr.hpu.edu.vn — career page)
#   3. Header `X-Org-Slug` = "Mã tổ chức" nhập ở trang đăng nhập trên domain chính
#      (hr.hpu.edu.vn không có subdomain). Chỉ là FALLBACK sau (1)+(2) — xem ADR-006.
#
# Sau khi resolve → set tenant context (contextvars) để database.py tự filter query,
# và reset context ở finally để không leak sang request khác.

from uuid import UUID

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.core.tenant_context import reset_current_org_id, set_current_org_id
from app.models.organization import Organization

settings = get_settings()

# Các path không thuộc tenant context
EXEMPT_PATHS = frozenset({"/health", "/docs", "/redoc", "/openapi.json"})


async def _resolve_org_id_by_slug(slug: str) -> UUID | None:
    """Tra organizations theo slug (bảng root, không bị tenant filter)."""
    # Import tại đây để tránh circular import (database import models.base)
    from app.database import async_session_factory

    async with async_session_factory() as session:
        result = await session.execute(
            select(Organization.id)
            .where(Organization.slug == slug)
            .where(Organization.status == "active")
        )
        return result.scalar_one_or_none()


def _extract_subdomain(host: str) -> str | None:
    """Lấy org slug từ Host header: hpu.talentchart.hpu.edu.vn → 'hpu'.

    Bỏ qua subdomain hệ thống (app, www, storage, api) và host không thuộc BASE_DOMAIN.
    """
    hostname = host.split(":")[0].lower()
    suffix = f".{settings.BASE_DOMAIN}"
    if not hostname.endswith(suffix):
        return None
    prefix = hostname[: -len(suffix)]
    # Chỉ nhận đúng 1 label (slug), không nhận a.b.talentchart...
    if not prefix or "." in prefix or prefix in settings.RESERVED_SUBDOMAINS:
        return None
    return prefix


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        org_id: UUID | None = None

        if request.url.path not in EXEMPT_PATHS:
            # 1) JWT claim (nguồn tin cậy nhất)
            payload = getattr(request.state, "token_payload", None)
            if payload and payload.get("organization_id"):
                try:
                    org_id = UUID(payload["organization_id"])
                except ValueError:
                    org_id = None

            # 2) Subdomain — ưu tiên X-Forwarded-Host (đi qua proxy/Next rewrites
            # thì Host bị thay bằng địa chỉ nội bộ của backend)
            if org_id is None:
                host = request.headers.get(
                    "x-forwarded-host", request.headers.get("host", "")
                )
                slug = _extract_subdomain(host)
                if slug:
                    org_id = await _resolve_org_id_by_slug(slug)

            # 3) Header X-Org-Slug = "Mã tổ chức" người dùng nhập ở trang đăng nhập
            # trên domain chính (hr.hpu.edu.vn KHÔNG có subdomain). Chỉ là FALLBACK:
            # JWT (1) và subdomain (2) luôn thắng nên header KHÔNG override được tenant
            # context đã xác định. Header chỉ CHỌN tổ chức để đăng nhập — vẫn phải có
            # credential hợp lệ, không cấp quyền gì thêm (ADR-006).
            if org_id is None:
                org_slug = request.headers.get("x-org-slug")
                if org_slug:
                    org_id = await _resolve_org_id_by_slug(org_slug.strip().lower())

        request.state.organization_id = org_id
        token = set_current_org_id(org_id)
        try:
            return await call_next(request)
        finally:
            # BẮT BUỘC reset — tránh leak tenant context sang request khác
            reset_current_org_id(token)
