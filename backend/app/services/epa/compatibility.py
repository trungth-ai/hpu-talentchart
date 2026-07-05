# ★ Độ tương hợp 2 người — PORT NGUYÊN XI từ Fortune HR v6.2 (server.js dòng 550-589)

from app.services.epa.tamhop import TAM_HOP, XUNG


def compatibility_score(zodiac_1: dict, zodiac_2: dict) -> dict:
    """Điểm tương hợp + ghi chú giữa 2 người (input: kết quả get_canchi_from_birth)."""
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
