# User schemas — Response KHÔNG include organization_id (tránh leak — rule số 6)

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: str
    org_role: str
    system_role: str
    status: str
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
