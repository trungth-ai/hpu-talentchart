# Test session schemas — flow gửi bài test DISC

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TestLinkCreate(BaseModel):
    candidate_id: UUID
    expires_hours: int = 72

    @field_validator("expires_hours")
    @classmethod
    def expires_in_range(cls, v: int) -> int:
        if not 1 <= v <= 24 * 30:
            raise ValueError("Thời hạn link phải từ 1 giờ đến 30 ngày")
        return v


class TestLinkResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    token: str
    test_url: str
    expires_at: datetime
    is_used: bool
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TestSubmission(BaseModel):
    # {"0": {"most": 0, "least": 2}, ...} — index câu hỏi → lựa chọn
    disc_answers: dict[str, dict[str, int]] = Field(default_factory=dict)
    # {"0": 4, "1": 3, ...} — Likert 1-5
    personality_answers: dict[str, int] = Field(default_factory=dict)

    @field_validator("disc_answers")
    @classmethod
    def validate_disc_answers(cls, v: dict) -> dict:
        if len(v) > 100:
            raise ValueError("Số câu trả lời DISC không hợp lệ")
        for ans in v.values():
            extra_keys = set(ans.keys()) - {"most", "least"}
            if extra_keys:
                raise ValueError("Câu trả lời DISC chỉ gồm most/least")
        return v

    @field_validator("personality_answers")
    @classmethod
    def validate_personality_answers(cls, v: dict) -> dict:
        if len(v) > 100:
            raise ValueError("Số câu trả lời không hợp lệ")
        for val in v.values():
            if not 1 <= val <= 5:
                raise ValueError("Điểm Likert phải từ 1 đến 5")
        return v


class PublicTestResult(BaseModel):
    """Kết quả trả cho ỨNG VIÊN — chỉ Behavioural Layer (DISC), không lộ phân tích nội bộ."""

    disc_scores: dict[str, int]
    disc_primary: str
    disc_secondary: str
    disc_profile: str
    personality_scores: dict[str, Any]


class AdminTestResult(PublicTestResult):
    """Kết quả đầy đủ cho HR — kèm phân tích + gợi ý phỏng vấn.

    LƯU Ý (Critical Business Rules): kết quả test chỉ là 1 TÍN HIỆU THAM KHẢO,
    không được là yếu tố quyết định duy nhất trong tuyển dụng.
    """

    analysis: dict[str, Any] | None
    ai_suggestions: dict[str, Any] | None
    overall_score: int | None
    recommendation: str | None
    completed_at: datetime | None
