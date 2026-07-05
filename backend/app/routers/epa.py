# EPA router — Eastern Personality Assessment (Sprint 5, port từ Fortune HR)
#
# QUY TẮC HIỂN THỊ (Critical Business Rules):
# - Eastern Layer (Can Chi/Nạp Âm/Mệnh/Tam hợp) mặc định TẮT — chỉ hoạt động khi
#   org.settings.eastern_layer_enabled = true
# - Dữ liệu ngày sinh chỉ dùng khi candidate đã epa_consent (NĐ 13/2023)
# - Kết quả EPA CHỈ là tín hiệu tham khảo, không phải yếu tố quyết định tuyển dụng

import random
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_hr_manager
from app.core.responses import success
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import BusinessRuleError, ResourceNotFound
from app.models.candidate import Candidate
from app.models.organization import Organization
from app.models.test_session import TestSession
from app.models.user import User
from app.services.epa import archetype, canchi, compatibility, narrative, team_suggest

router = APIRouter(prefix="/epa", tags=["epa"])

# Ghi kèm mọi response EPA — nhắc quy tắc nghiệp vụ
DISCLAIMER = (
    "Kết quả EPA chỉ là tín hiệu tham khảo, không được dùng làm "
    "yếu tố quyết định duy nhất trong tuyển dụng/nhân sự"
)


async def _require_eastern_layer(db: AsyncSession) -> None:
    """Eastern Layer phải được tenant bật chủ động (mặc định TẮT)."""
    org_id = get_current_org_id()
    result = await db.execute(
        select(Organization.settings).where(Organization.id == org_id)
    )
    settings = result.scalar_one_or_none() or {}
    if not settings.get("eastern_layer_enabled", False):
        raise BusinessRuleError(
            "Eastern Layer chưa được bật cho tổ chức — bật trong cài đặt tổ chức "
            "(settings.eastern_layer_enabled) trước khi dùng tính năng EPA"
        )


async def _get_candidate_with_birth(candidate_id: UUID, db: AsyncSession) -> Candidate:
    """Lấy candidate trong tenant + kiểm tra consent/dữ liệu sinh (NĐ 13/2023)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise ResourceNotFound("ứng viên/nhân sự")
    if not candidate.epa_consent:
        raise BusinessRuleError(
            f"{candidate.full_name} chưa đồng ý (opt-in) cho phép dùng dữ liệu ngày sinh"
        )
    if candidate.birth_date is None:
        raise BusinessRuleError(f"{candidate.full_name} chưa có dữ liệu ngày sinh")
    return candidate


def _zodiac_of(candidate: Candidate) -> dict:
    bd = candidate.birth_date
    return canchi.get_canchi_from_birth(bd.day, bd.month, bd.year)


@router.get("/today")
async def epa_today(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Can Chi hôm nay (dashboard) — port getTodayCanChi từ Fortune HR."""
    await _require_eastern_layer(db)
    return success(canchi.get_today_canchi())


@router.get("/candidates/{candidate_id}/zodiac")
async def candidate_zodiac(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Can Chi/Nạp Âm/Mệnh của 1 ứng viên/nhân sự (cần epa_consent + birth_date)."""
    await _require_eastern_layer(db)
    candidate = await _get_candidate_with_birth(candidate_id, db)
    return success(
        {
            "candidate_id": str(candidate.id),
            "full_name": candidate.full_name,
            "zodiac": _zodiac_of(candidate),
            "disclaimer": DISCLAIMER,
        }
    )


@router.get("/compatibility")
async def epa_compatibility(
    candidate1_id: UUID = Query(...),
    candidate2_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Độ tương hợp giữa 2 người — công thức gốc Fortune HR (tam hợp +25, xung −30)."""
    await _require_eastern_layer(db)
    if candidate1_id == candidate2_id:
        raise BusinessRuleError("Cần chọn 2 người khác nhau để xem độ tương hợp")

    c1 = await _get_candidate_with_birth(candidate1_id, db)
    c2 = await _get_candidate_with_birth(candidate2_id, db)
    z1, z2 = _zodiac_of(c1), _zodiac_of(c2)
    result = compatibility.compatibility_score(z1, z2)

    return success(
        {
            "person1": {"id": str(c1.id), "full_name": c1.full_name, "zodiac": z1},
            "person2": {"id": str(c2.id), "full_name": c2.full_name, "zodiac": z2},
            "score": result["score"],
            "notes": result["notes"],
            "disclaimer": DISCLAIMER,
        }
    )


async def _is_eastern_layer_enabled(db: AsyncSession) -> bool:
    org_id = get_current_org_id()
    result = await db.execute(
        select(Organization.settings).where(Organization.id == org_id)
    )
    settings = result.scalar_one_or_none() or {}
    return bool(settings.get("eastern_layer_enabled", False))


@router.get("/candidates/{candidate_id}/archetype")
async def candidate_archetype(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """12 Personality Archetype — fusion DISC + Mệnh + Tam hợp (ADR-005, Sprint 6).

    Thuộc BEHAVIOURAL LAYER (mặc định): không cần bật Eastern Layer.
    - Cần ứng viên đã hoàn thành bài test DISC.
    - Dữ liệu sinh (nếu có consent) được dùng NỘI BỘ cho fusion; chi tiết
      mệnh/tam hợp chỉ hiển thị khi org bật Eastern Layer.
    """
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise ResourceNotFound("ứng viên/nhân sự")

    # Kết quả DISC mới nhất (bắt buộc)
    test_result = await db.execute(
        select(TestSession)
        .where(TestSession.candidate_id == candidate.id)
        .where(TestSession.completed_at.isnot(None))
        .order_by(TestSession.completed_at.desc())
        .limit(1)
    )
    test = test_result.scalar_one_or_none()
    if test is None or not test.disc_profile:
        raise BusinessRuleError(
            f"{candidate.full_name} chưa hoàn thành bài test DISC — "
            "gửi bài test trước khi xem archetype"
        )

    # Eastern inputs — chỉ khi ứng viên đã opt-in và có ngày sinh (NĐ 13/2023)
    menh = dia_chi = None
    if candidate.epa_consent and candidate.birth_date:
        bd = candidate.birth_date
        zodiac = canchi.get_canchi_from_birth(bd.day, bd.month, bd.year)
        menh, dia_chi = zodiac["menh"], zodiac["dia_chi"]

    fusion_result = archetype.compute_archetype(test.disc_profile, menh, dia_chi)
    draft = archetype.build_narrative(
        candidate.full_name, fusion_result["archetype"], test.disc_profile, test.disc_scores
    )
    polished = await narrative.polish_narrative(draft)

    payload = {
        "candidate_id": str(candidate.id),
        "full_name": candidate.full_name,
        "disc_profile": test.disc_profile,
        "disc_scores": test.disc_scores,
        "archetype": fusion_result["archetype"],
        "narrative": polished,
        "used_eastern_data": fusion_result["used_eastern_data"],
        "disclaimer": DISCLAIMER,
    }
    # Chi tiết fusion (nhắc đến Mệnh/Tam hợp) chỉ hiện khi Eastern Layer bật
    if await _is_eastern_layer_enabled(db):
        payload["fusion"] = fusion_result["fusion"]

    return success(payload)


class TeamSuggestRequest(BaseModel):
    size: int
    department: str | None = None
    candidate_type: str = "employee"

    @field_validator("size")
    @classmethod
    def size_in_range(cls, v: int) -> int:
        if not 2 <= v <= 20:
            raise ValueError("Quy mô đội phải từ 2 đến 20 người")
        return v


@router.post("/team-suggest")
async def epa_team_suggest(
    data: TeamSuggestRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Gợi ý đội nhóm theo tam hợp (thuật toán gốc: 3 phương án ngẫu nhiên, xếp hạng)."""
    await _require_eastern_layer(db)

    org_id = get_current_org_id()
    query = (
        select(Candidate)
        .where(Candidate.organization_id == org_id)
        .where(Candidate.status == "active")
        .where(Candidate.candidate_type == data.candidate_type)
        .where(Candidate.epa_consent.is_(True))
        .where(Candidate.birth_date.isnot(None))
    )
    if data.department:
        query = query.where(Candidate.department == data.department)

    result = await db.execute(query)
    candidates = result.scalars().all()

    members = [
        {
            "id": str(c.id),
            "full_name": c.full_name,
            "department": c.department,
            "position": c.position,
            "zodiac": _zodiac_of(c),
        }
        for c in candidates
    ]

    teams = team_suggest.suggest_teams(members, size=data.size, rng=random.Random())
    return success(
        {
            "eligible_count": len(members),
            "teams": teams,
            "disclaimer": DISCLAIMER,
        },
        message=(
            "Không đủ người đủ điều kiện (đã opt-in + có ngày sinh) để xếp đội"
            if not teams
            else "Đã gợi ý đội nhóm"
        ),
    )
