# Organization schemas — đọc thông tin tổ chức + cập nhật cài đặt (chỉ admin/owner sửa).

from typing import Any
from uuid import UUID

from pydantic import BaseModel


class OrgSettingsUpdate(BaseModel):
    """Cập nhật một phần settings (chỉ gửi field muốn đổi)."""

    eastern_layer_enabled: bool | None = None
    google_workspace_domain: str | None = None
    google_auto_provision: bool | None = None


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    settings: dict[str, Any]

    model_config = {"from_attributes": True}
