# EPA router — Eastern Personality Assessment (Sprint 5, port từ Fortune HR)
#
# QUY TẮC HIỂN THỊ (Critical Business Rules):
# - Eastern Layer (Can Chi/Nạp Âm/Mệnh/Tam hợp) mặc định TẮT — chỉ hoạt động khi
#   org.settings.eastern_layer_enabled = true
# - Dữ liệu ngày sinh chỉ dùng khi candidate đã epa_consent (NĐ 13/2023)
# - Kết quả EPA CHỈ là tín hiệu tham khảo, không phải yếu tố quyết định tuyển dụng

import asyncio
import random
from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_hr_manager
from app.core.responses import success
from app.core.tenant_context import get_current_org_id
from app.data.horoscope import get_sign_by_date
from app.data.zodiac_animals import ZODIAC_ANIMALS, get_animal_by_dia_chi
from app.database import get_db
from app.exceptions import BusinessRuleError, ResourceNotFound
from app.models.astrology import AstrologyReference
from app.models.candidate import Candidate
from app.models.organization import Organization
from app.models.test_session import TestSession
from app.models.user import User
from app.services.epa import (
    archetype,
    biorhythm,
    canchi,
    compatibility,
    fortune,
    fortune_content_store,
    narrative,
    team_suggest,
)

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


VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def _today_vn():
    """Ngày hiện tại theo giờ Việt Nam (Asia/Ho_Chi_Minh) — tránh lệch ngày do server UTC."""
    return datetime.now(VN_TZ).date()


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
    return success(canchi.get_today_canchi(_today_vn()))


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
    result = compatibility.compatibility_score(z1, z2)  # điểm + notes gốc (parity)
    rel = compatibility.relationship(z1["dia_chi"], z2["dia_chi"])  # quan hệ trung tính giới
    notes = [*result["notes"], rel["description"]]
    fe = compatibility.five_elements_note(z1.get("menh"), z2.get("menh"))
    if fe:
        notes.append(fe)

    # Mô tả HÔN NHÂN theo sách con giáp — CHỈ áp dụng cho cặp NAM–NỮ (tránh khung vợ chồng
    # khi so 2 người cùng giới). Lấy theo góc nhìn người NAM: "nam tuổi X và cô ấy (nữ) tuổi Y".
    detail = None
    detail_note = None
    g1, g2 = c1.gender, c2.gender
    if g1 and g2 and g1 != g2:
        male_c = c1 if g1 == "male" else c2
        female_c = c2 if g1 == "male" else c1
        mz = _zodiac_of(male_c)["dia_chi"]
        fz = _zodiac_of(female_c)["dia_chi"]
        row = await db.get(AstrologyReference, ("compat", mz))
        if row:
            detail = (row.content.get("male") or {}).get(fz)
        if not detail:
            # Tra ngược: góc nhìn người NỮ ("nữ tuổi F và anh ấy tuổi M") — cùng cặp,
            # giúp phủ các tuổi mà vai nam không có trong sách (Dần/Tỵ/Ngọ...).
            frow = await db.get(AstrologyReference, ("compat", fz))
            if frow:
                detail = (frow.content.get("female") or {}).get(mz)
        if detail:
            detail_note = (
                f"Về hôn nhân/tình duyên (nam {male_c.full_name} – nữ {female_c.full_name})"
            )
    elif g1 and g2:
        detail_note = (
            "Hai người cùng giới — chỉ xét tương hợp tuổi (công việc/hợp tác), "
            "không luận hôn nhân."
        )
    else:
        detail_note = (
            "Thiếu thông tin giới tính — hiển thị tương hợp tuổi chung; "
            "bổ sung giới tính để xem thêm góc nhìn hôn nhân."
        )

    return success(
        {
            "person1": {
                "id": str(c1.id),
                "full_name": c1.full_name,
                "gender": c1.gender,
                "zodiac": z1,
            },
            "person2": {
                "id": str(c2.id),
                "full_name": c2.full_name,
                "gender": c2.gender,
                "zodiac": z2,
            },
            "score": result["score"],
            "relationship": rel,   # {name, description} — trung tính giới, mọi cặp
            "notes": notes,
            "detail": detail,          # mô tả hôn nhân (chỉ cặp nam–nữ, có thể None)
            "detail_note": detail_note,
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


@router.get("/candidates/{candidate_id}/personality")
async def candidate_personality(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Tính cách đặc trưng theo NGÀY SINH: cung hoàng đạo (chiêm tinh phương Tây) + con giáp.

    KHÔNG cần bật Eastern Layer (đây là mô tả tính cách tham khảo), nhưng cần ứng viên đã
    opt-in (epa_consent) và có birth_date (NĐ 13/2023). Nội dung cung hoàng đạo lấy từ tài
    liệu Trung cung cấp; chi tiết tính cách theo con giáp sẽ bổ sung khi có tài liệu nguồn.
    """
    candidate = await _get_candidate_with_birth(candidate_id, db)
    bd = candidate.birth_date
    horoscope = get_sign_by_date(bd)
    zodiac = canchi.get_canchi_from_birth(bd.day, bd.month, bd.year)
    zodiac_personality = get_animal_by_dia_chi(zodiac["dia_chi"])

    return success(
        {
            "candidate_id": str(candidate.id),
            "full_name": candidate.full_name,
            "horoscope": horoscope,
            "zodiac_summary": {
                "con_giap": zodiac["con_giap"],
                "emoji": zodiac["emoji"],
                "tuoi_am": zodiac["tuoi_am"],
                "menh": zodiac["menh"],
            },
            # Tính cách theo con giáp (địa chi) — từ tài liệu "12 con giáp theo lịch vạn niên"
            "zodiac_personality": zodiac_personality,
            "disclaimer": DISCLAIMER,
        }
    )


@router.get("/candidates/{candidate_id}/fortune")
async def candidate_fortune(
    candidate_id: UUID,
    ai: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Vận trình NGÀY + THÁNG — Can Chi tính offline (nhanh). CHỈ gọi Claude diễn giải khi ai=true.

    Mặc định ai=false: trả Can Chi + chỉ nam theo sách, KHÔNG gọi AI (tải nhanh, giảm chi phí).
    Cần epa_consent + birth_date.
    """
    candidate = await _get_candidate_with_birth(candidate_id, db)
    bd = candidate.birth_date
    z = canchi.get_canchi_from_birth(bd.day, bd.month, bd.year)
    sign = get_sign_by_date(bd)
    tc = canchi.get_today_canchi(_today_vn())
    today = _today_vn()

    day_facts = (
        f"Hôm nay dương lịch {tc['solar_date']}, âm lịch {tc['lunar_date']}, "
        f"ngày {tc['day_canchi']}, năm {tc['year_canchi']}. Nhân sự {candidate.full_name} "
        f"tuổi {z['con_giap']} ({z['tuoi_am']}, mệnh {z['menh']}), "
        f"cung hoàng đạo {sign['name']} ({sign['element']})."
    )
    # Chỉ nam vận trình tháng theo sách (nếu đã seed) — đưa vào facts để Claude bám sát
    month_row = await db.get(AstrologyReference, ("month", sign["code"]))
    month_guidance = month_row.content.get(str(today.month)) if month_row else None
    month_facts = (
        f"Tháng {today.month}/{today.year} dương lịch. Nhân sự {candidate.full_name} "
        f"tuổi {z['con_giap']} (mệnh {z['menh']}), cung hoàng đạo "
        f"{sign['name']} ({sign['element']})."
    )
    if month_guidance:
        month_facts += (
            f" Chỉ nam vận trình tháng {today.month} (theo sách) cho cung "
            f"{sign['name']}: {month_guidance}"
        )
    # Mặc định KHÔNG gọi AI (tải nhanh, giảm chi phí) — chỉ diễn giải khi ?ai=true (bấm nút).
    if ai:
        day_narr, month_narr = await asyncio.gather(
            fortune.fortune_narrative("day", day_facts),
            fortune.fortune_narrative("month", month_facts),
        )
    else:
        day_narr, month_narr = None, None
    return success(
        {
            "candidate_id": str(candidate.id),
            "full_name": candidate.full_name,
            "birth": {"day": bd.day, "month": bd.month, "year": bd.year},
            "day": {"canchi": tc, "narrative": day_narr},
            "month": {
                "month": today.month,
                "year": today.year,
                "narrative": month_narr,
                "book_guidance": month_guidance,
            },
            "ai_generated": ai and bool(fortune.settings.ANTHROPIC_API_KEY),
            "disclaimer": DISCLAIMER,
        }
    )


@router.get("/candidates/{candidate_id}/lichngaytot")
async def candidate_lichngaytot(
    candidate_id: UUID,
    on_date: date | None = Query(None, alias="date"),
    period: str = Query("day"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Tử vi theo KỲ (day/week/month/year) cho ứng viên — ĐỌC TỪ DB (bảng fortune_content).

    Cào theo lô định kỳ (Celery beat). Kỳ hiện tại nếu DB còn thiếu thì tự cào bù rồi lưu
    (lần sau khỏi cào + giảm gọi AI). Xem kỳ trước qua ?date=YYYY-MM-DD (lấy kỳ chứa ngày đó).
    Cần epa_consent + birth_date.
    """
    if period not in fortune_content_store.PERIODS:
        raise BusinessRuleError("Kỳ không hợp lệ (day | week | month | year)")
    candidate = await _get_candidate_with_birth(candidate_id, db)
    bd = candidate.birth_date
    z = canchi.get_canchi_from_birth(bd.day, bd.month, bd.year)
    sign = get_sign_by_date(bd)
    today = _today_vn()
    target = on_date or today
    if target > today:
        raise BusinessRuleError("Chưa có tử vi cho kỳ trong tương lai")
    data = await fortune_content_store.get_fortune(
        db,
        period_type=period,
        dia_chi=z["dia_chi"],
        sign_code=sign["code"],
        on_date=target,
        today=today,
    )
    if not any(data.get(k) for k in ("day", "zodiac", "horoscope")):
        raise BusinessRuleError(
            "Chưa có dữ liệu tử vi cho kỳ này (dữ liệu được cào tự động định kỳ)"
        )
    return success({**data, "disclaimer": DISCLAIMER})


@router.get("/candidates/{candidate_id}/biorhythm")
async def candidate_biorhythm(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Nhịp sinh học (Biorhythm) quanh hôm nay — cần epa_consent + birth_date.

    Trả giá trị 3 nhịp (thể chất/cảm xúc/trí tuệ) hôm nay + chuỗi ±14 ngày để vẽ biểu đồ.
    """
    candidate = await _get_candidate_with_birth(candidate_id, db)
    today = _today_vn()
    now = biorhythm.biorhythm_today(candidate.birth_date, today)
    return success(
        {
            "candidate_id": str(candidate.id),
            "full_name": candidate.full_name,
            "date": today.isoformat(),
            "days_alive": now["days_alive"],
            "today": {k: now[k] for k in ("physical", "emotional", "intellectual")},
            "series": biorhythm.biorhythm_series(candidate.birth_date, today, span=14),
            "disclaimer": DISCLAIMER,
        }
    )


@router.get("/stats/zodiac")
async def zodiac_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Thống kê số nhân sự theo 12 CON GIÁP trong đơn vị (dashboard).

    Chỉ tính người active có epa_consent + birth_date. Trả theo thứ tự Tý→Hợi.
    """
    org_id = get_current_org_id()
    result = await db.execute(
        select(Candidate)
        .where(Candidate.organization_id == org_id)
        .where(Candidate.status == "active")
        .where(Candidate.epa_consent.is_(True))
        .where(Candidate.birth_date.is_not(None))
    )
    counts = {dc: 0 for dc in ZODIAC_ANIMALS}
    for c in result.scalars().all():
        dc = _zodiac_of(c)["dia_chi"]
        if dc in counts:
            counts[dc] += 1
    by_zodiac = [
        {"dia_chi": dc, "animal": ZODIAC_ANIMALS[dc]["animal"], "count": counts[dc]}
        for dc in ZODIAC_ANIMALS
    ]
    return success({"total": sum(counts.values()), "by_zodiac": by_zodiac})


@router.get("/reference/{kind}/{key}")
async def astrology_reference(
    kind: str,
    key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_hr_manager),
):
    """Nội dung tử vi ĐẦY ĐỦ (toàn diện) — dùng cho nút "Xem thêm".

    - kind=zodiac, key=địa chi (Tý, Sửu, ...): toàn bộ nội dung con giáp.
    - kind=horoscope, key=code cung (ARIES, ...): toàn bộ nội dung cung hoàng đạo (2 nguồn).
    Dữ liệu nạp từ tài liệu nguồn qua scripts/seed_astrology.py (bảng astrology_reference).
    """
    from app.services.epa.reference_clean import clean_content

    if kind not in ("zodiac", "horoscope"):
        raise BusinessRuleError("Loại tra cứu không hợp lệ")
    obj = await db.get(AstrologyReference, (kind, key))
    if obj is None:
        raise ResourceNotFound("nội dung tử vi (chưa nạp dữ liệu?)")
    return success(
        {
            "kind": obj.kind,
            "key": obj.key,
            "title": obj.title,
            "content": clean_content(obj.content),
            "disclaimer": DISCLAIMER,
        }
    )


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
