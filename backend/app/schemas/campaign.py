# Campaign schemas — Create KHÔNG có organization_id (rule 4), Response KHÔNG leak org_id (rule 6)

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.models.campaign import CAMPAIGN_STATUSES


class CampaignCreate(BaseModel):
    name: str
    position: str
    department: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    target_headcount: int = 1
    salary_min: int | None = None  # Integer VNĐ
    salary_max: int | None = None  # Integer VNĐ

    @field_validator("name", "position")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Không được để trống")
        return v.strip()

    @field_validator("target_headcount")
    @classmethod
    def headcount_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Chỉ tiêu tuyển dụng phải >= 1")
        return v

    @field_validator("salary_min", "salary_max")
    @classmethod
    def salary_non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Lương phải >= 0")
        return v

    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("Lương tối đa phải >= lương tối thiểu")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Ngày kết thúc phải >= ngày bắt đầu")
        return self


class CampaignUpdate(CampaignCreate):
    # PUT là partial update (api-conventions.md) — mọi field optional
    name: str | None = None
    position: str | None = None
    target_headcount: int | None = None
    status: str | None = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in CAMPAIGN_STATUSES:
            raise ValueError(f"Trạng thái không hợp lệ (chọn: {', '.join(CAMPAIGN_STATUSES)})")
        return v

    @field_validator("name", "position")
    @classmethod
    def must_not_be_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Không được để trống")
        return v.strip() if v else v

    @field_validator("target_headcount")
    @classmethod
    def headcount_positive(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Chỉ tiêu tuyển dụng phải >= 1")
        return v


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    position: str
    department: str | None
    description: str | None
    start_date: date | None
    end_date: date | None
    target_headcount: int
    salary_min: int | None
    salary_max: int | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
