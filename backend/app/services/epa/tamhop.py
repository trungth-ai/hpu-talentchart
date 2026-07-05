# ★ Tam hợp / Tứ hành xung — PORT NGUYÊN XI từ Fortune HR v6.2 (server.js dòng 503-530)

TAM_HOP = [
    ["Thân", "Tý", "Thìn"],
    ["Tỵ", "Dậu", "Sửu"],
    ["Dần", "Ngọ", "Tuất"],
    ["Hợi", "Mão", "Mùi"],
]

XUNG = [
    ["Tý", "Ngọ"], ["Sửu", "Mùi"], ["Dần", "Thân"],
    ["Mão", "Dậu"], ["Thìn", "Tuất"], ["Tỵ", "Hợi"],
]


def get_tam_hop_group(dia_chi: str) -> list[str] | None:
    """Nhóm tam hợp chứa địa chi này (None nếu chi không hợp lệ)."""
    for group in TAM_HOP:
        if dia_chi in group:
            return group
    return None


def pair_score(dia_chi_1: str, dia_chi_2: str) -> int:
    """Điểm tương hợp 1 cặp địa chi — công thức gốc: 50, +25 tam hợp, −30 xung, kẹp 0-100."""
    score = 50
    for group in TAM_HOP:
        if dia_chi_1 in group and dia_chi_2 in group:
            score += 25
    for pair in XUNG:
        if dia_chi_1 in pair and dia_chi_2 in pair:
            score -= 30
    return min(100, max(0, score))
