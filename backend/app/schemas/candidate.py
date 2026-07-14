# Candidate schemas
# - Create KHÔNG có organization_id / pipeline_stage (pipeline chỉ đổi qua endpoint riêng)
# - Dữ liệu ngày/giờ/nơi sinh CHỈ nhận khi epa_consent=True (NĐ 13/2023 — opt-in)

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, model_validator

from app.models.candidate import CANDIDATE_TYPES


class CandidateBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    candidate_type: str = "applicant"
    position: str | None = None
    source: str | None = None
    notes: str | None = None
    campaign_id: UUID | None = None
    department_id: UUID | None = None  # gán vào phòng ban (cơ cấu tổ chức)

    # Dành cho candidate_type=employee (hợp nhất nhân sự)
    employee_code: str | None = None
    department: str | None = None

    # Giới tính ('male'|'female') — dùng cho so sánh tương hợp cho tinh tế; KHÔNG nhạy cảm
    gender: str | None = None

    @field_validator("gender")
    @classmethod
    def gender_valid(cls, v: str | None) -> str | None:
        if v not in (None, "", "male", "female"):
            raise ValueError("Giới tính chỉ nhận 'male' hoặc 'female'")
        return v or None

    # EPA opt-in
    epa_consent: bool = False
    birth_date: date | None = None
    birth_time: str | None = None  # "HH:MM"
    birth_place: str | None = None

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Họ tên không được để trống")
        return v.strip()

    @field_validator("candidate_type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        if v not in CANDIDATE_TYPES:
            raise ValueError(f"Loại ứng viên không hợp lệ (chọn: {', '.join(CANDIDATE_TYPES)})")
        return v

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
        # Không có consent thì KHÔNG được lưu bất kỳ dữ liệu sinh nào
        has_birth_data = any([self.birth_date, self.birth_time, self.birth_place])
        if has_birth_data and not self.epa_consent:
            raise ValueError(
                "Dữ liệu ngày/giờ/nơi sinh chỉ được lưu khi ứng viên đồng ý (epa_consent)"
            )
        return self


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(CandidateBase):
    # PUT partial update — mọi field optional; pipeline_stage KHÔNG đổi được ở đây
    full_name: str | None = None
    email: EmailStr | None = None
    candidate_type: str | None = None
    epa_consent: bool | None = None

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Họ tên không được để trống")
        return v.strip() if v else v

    @field_validator("candidate_type")
    @classmethod
    def type_must_be_valid(cls, v: str | None) -> str | None:
        if v is not None and v not in CANDIDATE_TYPES:
            raise ValueError(f"Loại ứng viên không hợp lệ (chọn: {', '.join(CANDIDATE_TYPES)})")
        return v

    @model_validator(mode="after")
    def epa_data_requires_consent(self):
        # Với update: chỉ chặn khi client vừa gửi birth data vừa tắt/không bật consent
        has_birth_data = any([self.birth_date, self.birth_time, self.birth_place])
        if has_birth_data and self.epa_consent is not True:
            raise ValueError(
                "Dữ liệu ngày/giờ/nơi sinh chỉ được cập nhật kèm epa_consent=true"
            )
        return self


class PipelineTransition(BaseModel):
    target_stage: str


class CandidateResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str | None
    candidate_type: str
    pipeline_stage: str
    position: str | None
    source: str | None
    notes: str | None
    campaign_id: UUID | None
    department_id: UUID | None
    employee_code: str | None
    department: str | None
    gender: str | None
    epa_consent: bool
    # birth_date/birth_time/birth_place KHÔNG trả trong list/detail mặc định
    # (dữ liệu nhạy cảm — chỉ EPA Engine dùng nội bộ, Sprint 5)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
