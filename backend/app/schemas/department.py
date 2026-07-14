# Department schemas — cơ cấu tổ chức (phòng ban dạng cây). KHÔNG có organization_id (rule số 4).

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class DepartmentCreate(BaseModel):
    name: str
    parent_id: UUID | None = None
    manager_user_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tên phòng ban không được để trống")
        return v.strip()


class DepartmentUpdate(BaseModel):
    name: str | None = None
    parent_id: UUID | None = None
    manager_user_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Tên phòng ban không được để trống")
        return v.strip() if v else v


class DepartmentResponse(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None
    manager_user_id: UUID | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
