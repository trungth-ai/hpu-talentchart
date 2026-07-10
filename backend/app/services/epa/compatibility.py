# ★ Độ tương hợp 2 người — compatibility_score() PORT NGUYÊN XI từ Fortune HR v6.2
# (server.js 550-589), GIỮ NGUYÊN để parity 300 case không đổi.
# relationship() bổ sung: quan hệ tuổi TRUYỀN THỐNG, TRUNG TÍNH giới (tam/lục hợp,
# lục xung/hại) — dùng cho UI so sánh 2 người bất kỳ (KHÔNG khung "vợ chồng").

from app.services.epa.tamhop import TAM_HOP, XUNG

# Dữ liệu quan hệ truyền thống (địa chi) — độc lập, trung tính giới.
_TAM_HOP_SETS = [
    {"Thân", "Tý", "Thìn"},
    {"Dần", "Ngọ", "Tuất"},
    {"Tỵ", "Dậu", "Sửu"},
    {"Hợi", "Mão", "Mùi"},
]
_LUC_HOP = [
    {"Tý", "Sửu"}, {"Dần", "Hợi"}, {"Mão", "Tuất"},
    {"Thìn", "Dậu"}, {"Tỵ", "Thân"}, {"Ngọ", "Mùi"},
]
_LUC_XUNG = [
    {"Tý", "Ngọ"}, {"Sửu", "Mùi"}, {"Dần", "Thân"},
    {"Mão", "Dậu"}, {"Thìn", "Tuất"}, {"Tỵ", "Hợi"},
]
_LUC_HAI = [
    {"Tý", "Mùi"}, {"Sửu", "Ngọ"}, {"Dần", "Tỵ"},
    {"Mão", "Thìn"}, {"Thân", "Hợi"}, {"Dậu", "Tuất"},
]


def compatibility_score(zodiac_1: dict, zodiac_2: dict) -> dict:
    """Điểm tương hợp + ghi chú giữa 2 người (input: kết quả get_canchi_from_birth).

    GIỮ NGUYÊN thuật toán gốc (parity Fortune HR) — không đổi score/notes.
    """
    score = 50
    notes: list[str] = []

    for group in TAM_HOP:
        if zodiac_1["dia_chi"] in group and zodiac_2["dia_chi"] in group:
            score += 25
            notes.append("Tam hợp: Rất tương hợp")

    for pair in XUNG:
        if zodiac_1["dia_chi"] in pair and zodiac_2["dia_chi"] in pair:
            score -= 30
            notes.append("Xung: Dễ mâu thuẫn")

    return {"score": min(100, max(0, score)), "notes": notes}


def relationship(dia_chi_1: str, dia_chi_2: str) -> dict:
    """Quan hệ tuổi truyền thống (trung tính giới) → tên + mô tả, hợp mọi cặp người.

    Ngũ hành tương sinh/khắc và mô tả hôn nhân theo sách được xử lý ở tầng router.
    """
    pair = {dia_chi_1, dia_chi_2}
    if dia_chi_1 == dia_chi_2:
        return {
            "name": "Cùng tuổi",
            "description": "Cùng con giáp — dễ đồng cảm, hiểu ý nhau; nhưng có thể cùng điểm yếu nên cần bổ khuyết cho nhau.",
        }
    for g in _TAM_HOP_SETS:
        if pair <= g:
            return {
                "name": "Tam hợp",
                "description": "Rất hợp: dễ đồng lòng, tin tưởng và hỗ trợ nhau tốt trong công việc, hợp tác.",
            }
    if pair in _LUC_HOP:
        return {
            "name": "Lục hợp (nhị hợp)",
            "description": "Hợp ý, bổ trợ cho nhau, phối hợp ăn ý và bền.",
        }
    if pair in _LUC_XUNG:
        return {
            "name": "Lục xung",
            "description": "Dễ va chạm quan điểm, tính cách trái ngược — cần lắng nghe và nhường nhịn khi phối hợp.",
        }
    if pair in _LUC_HAI:
        return {
            "name": "Lục hại",
            "description": "Dễ hiểu lầm, kỳ vọng lệch nhau — nên trao đổi rõ ràng khi làm việc cùng.",
        }
    return {
        "name": "Bình hòa",
        "description": "Không xung không hợp đặc biệt — phối hợp ở mức bình thường, tùy nỗ lực hai bên.",
    }


def five_elements_note(menh_1: str | None, menh_2: str | None) -> str | None:
    """Ghi chú ngũ hành tương sinh/tương khắc giữa 2 mệnh (nếu có)."""
    if not menh_1 or not menh_2:
        return None
    sinh = {("Thủy", "Mộc"), ("Mộc", "Hỏa"), ("Hỏa", "Thổ"), ("Thổ", "Kim"), ("Kim", "Thủy")}
    khac = {("Thủy", "Hỏa"), ("Hỏa", "Kim"), ("Kim", "Mộc"), ("Mộc", "Thổ"), ("Thổ", "Thủy")}
    if (menh_1, menh_2) in sinh or (menh_2, menh_1) in sinh:
        return f"Ngũ hành tương sinh (Mệnh {menh_1} ↔ {menh_2}) — hỗ trợ nhau."
    if (menh_1, menh_2) in khac or (menh_2, menh_1) in khac:
        return f"Ngũ hành tương khắc (Mệnh {menh_1} ↔ {menh_2}) — cần dung hòa."
    return None
