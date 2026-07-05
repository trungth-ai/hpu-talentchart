# JobPost schemas — admin CRUD + public career page

import re
import unicodedata
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator


def slugify(text: str) -> str:
    """Chuyển tiếng Việt có dấu thành slug URL: 'Giảng viên CNTT' → 'giang-vien-cntt'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return text or "tin-tuyen-dung"


class JobPostCreate(BaseModel):
    title: str
    slug: str | None = None  # None → tự sinh từ title
    description: str | None = None
    requirements: str | None = None
    benefits: str | None = None
    location: str | None = None
    salary_min: int | None = None  # Integer VNĐ
    salary_max: int | None = None
    campaign_id: UUID | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tiêu đề không được để trống")
        return v.strip()

    @field_validator("salary_min", "salary_max")
    @classmethod
    def salary_non_negative(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Lương phải >= 0")
        return v

    @model_validator(mode="after")
    def normalize(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("Lương tối đa phải >= lương tối thiểu")
        if not self.slug:
            self.slug = slugify(self.title)
        else:
            self.slug = slugify(self.slug)
        return self


class JobPostUpdate(JobPostCreate):
    title: str | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Tiêu đề không được để trống")
        return v.strip() if v else v

    @model_validator(mode="after")
    def normalize(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_max < self.salary_min
        ):
            raise ValueError("Lương tối đa phải >= lương tối thiểu")
        if self.slug:
            self.slug = slugify(self.slug)
        return self


class JobPostResponse(BaseModel):
    id: UUID
    title: str
    slug: str
    description: str | None
    requirements: str | None
    benefits: str | None
    location: str | None
    salary_min: int | None
    salary_max: int | None
    campaign_id: UUID | None
    is_published: bool
    published_at: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicJobResponse(BaseModel):
    """Bản public — không lộ campaign_id/status nội bộ."""

    id: UUID
    title: str
    slug: str
    description: str | None
    requirements: str | None
    benefits: str | None
    location: str | None
    salary_min: int | None
    salary_max: int | None
    published_at: datetime | None

    model_config = {"from_attributes": True}


class PublicApplication(BaseModel):
    """Đơn ứng tuyển từ Career Page — tạo Candidate ở trạng thái NEW."""

    full_name: str
    email: EmailStr
    phone: str | None = None
    notes: str | None = None

    # EPA opt-in ngay từ form ứng tuyển (không bắt buộc)
    epa_consent: bool = False
    birth_date: date | None = None  # YYYY-MM-DD (db-conventions.md)
    birth_time: str | None = None  # HH:MM
    birth_place: str | None = None

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Họ tên không được để trống")
        return v.strip()

    @field_validator("birth_time")
    @classmethod
    def birth_time_format(cls, v: str | None) -> str | None:
        if v is None:
            return v
        parts = v.split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError("Giờ sinh phải theo định dạng HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if hour > 23 or minute > 59:
            raise ValueError("Giờ sinh không hợp lệ")
        return f"{hour:02d}:{minute:02d}"

    @model_validator(mode="after")
    def epa_data_requires_consent(self):
        has_birth_data = any([self.birth_date, self.birth_time, self.birth_place])
        if has_birth_data and not self.epa_consent:
            raise ValueError(
                "Dữ liệu ngày/giờ/nơi sinh chỉ được gửi khi bạn đồng ý (epa_consent)"
            )
        return self
