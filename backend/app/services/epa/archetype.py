# ★ 12 Personality Archetype — fusion DISC + Mệnh + Tam hợp (ADR-005, Sprint 6)
#
# Thuật toán XÁC ĐỊNH (deterministic):
#   1. Archetype base theo DISC profile: +2 điểm
#   2. Archetype của profile đảo (secondary/primary): +1 điểm
#   3. Mệnh (nếu có dữ liệu sinh + consent): +1 cho 2 archetype cùng hành
#   4. Tam hợp: +1 cho 3 archetype cùng nhóm địa chi
#   → Điểm cao nhất thắng; hòa điểm → archetype base DISC thắng.
#
# Không có dữ liệu Eastern → kết quả = base DISC (Behavioural Layer vẫn đầy đủ).

from typing import Any

from app.data.archetypes import (
    ARCHETYPES,
    DISC_TO_ARCHETYPE,
    MENH_AFFINITY,
    TAMHOP_AFFINITY,
)


def _base_archetype(disc_profile: str) -> str:
    """Archetype gốc theo DISC profile; profile lạ → dùng primary."""
    if disc_profile in DISC_TO_ARCHETYPE:
        return DISC_TO_ARCHETYPE[disc_profile]
    primary = disc_profile.split("/")[0]
    return DISC_TO_ARCHETYPE.get(primary, "HARMONIZER")


def _reversed_profile(disc_profile: str) -> str | None:
    """'C/I' → 'I/C'; profile đơn không có bản đảo."""
    if "/" not in disc_profile:
        return None
    primary, secondary = disc_profile.split("/", 1)
    return f"{secondary}/{primary}"


def compute_archetype(
    disc_profile: str,
    menh: str | None = None,
    dia_chi: str | None = None,
) -> dict[str, Any]:
    """Fusion ra archetype + bảng điểm giải thích (transparent, test được)."""
    scores: dict[str, int] = dict.fromkeys(ARCHETYPES, 0)
    reasons: list[str] = []

    base = _base_archetype(disc_profile)
    scores[base] += 2
    reasons.append(f"DISC {disc_profile} → {base} (+2)")

    reversed_profile = _reversed_profile(disc_profile)
    if reversed_profile and reversed_profile in DISC_TO_ARCHETYPE:
        alt = DISC_TO_ARCHETYPE[reversed_profile]
        if alt != base:
            scores[alt] += 1
            reasons.append(f"DISC đảo {reversed_profile} → {alt} (+1)")

    if menh and menh in MENH_AFFINITY:
        for code in MENH_AFFINITY[menh]:
            scores[code] += 1
        reasons.append(f"Mệnh {menh} → {'/'.join(MENH_AFFINITY[menh])} (+1)")

    if dia_chi and dia_chi in TAMHOP_AFFINITY:
        for code in TAMHOP_AFFINITY[dia_chi]:
            scores[code] += 1
        reasons.append(f"Tam hợp ({dia_chi}) → {'/'.join(TAMHOP_AFFINITY[dia_chi])} (+1)")

    # Chọn điểm cao nhất; hòa → base DISC thắng (deterministic)
    max_score = max(scores.values())
    winners = [code for code, s in scores.items() if s == max_score]
    winner = base if base in winners else sorted(winners)[0]

    return {
        "archetype": ARCHETYPES[winner],
        "code": winner,
        "used_eastern_data": bool(menh or dia_chi),
        "fusion": {
            "scores": {k: v for k, v in scores.items() if v > 0},
            "reasons": reasons,
        },
    }


def build_narrative(
    full_name: str,
    archetype: dict[str, Any],
    disc_profile: str,
    disc_scores: dict[str, int] | None = None,
) -> str:
    """Narrative tiếng Việt từ template (fallback khi không có Claude API).

    Production có ANTHROPIC_API_KEY sẽ dùng narrative_service.polish_narrative()
    để Claude API trau chuốt (cache Redis 30 ngày — HUONG-DAN risk #4).
    """
    strengths = "; ".join(archetype["strengths"][:3])
    watchouts = "; ".join(archetype["watchouts"][:2])
    score_text = ""
    if disc_scores:
        top = sorted(disc_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        score_text = " và ".join(f"{k} ({v}%)" for k, v in top)
        score_text = f" Hai khuynh hướng nổi bật nhất của bạn là {score_text}."

    return (
        f"{full_name} thuộc nhóm {archetype['name_vi']} ({archetype['name_en']}) — "
        f"{archetype['tagline'].lower()}.{score_text} "
        f"{archetype['description']} "
        f"Điểm mạnh nổi bật: {strengths}. "
        f"Điểm cần lưu ý: {watchouts}. "
        f"Gợi ý môi trường phù hợp: {archetype['university_fit']}"
    )
