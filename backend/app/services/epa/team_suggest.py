# ★ Gợi ý đội nhóm theo tam hợp — PORT từ Fortune HR v6.2 (server.js dòng 500-547)
# Giữ nguyên thuật toán: xáo trộn ngẫu nhiên 3 lần, chấm điểm trung bình từng cặp,
# xếp hạng giảm dần. RNG inject được để test tái lập.

import random
from typing import Any

from app.services.epa.tamhop import pair_score


def suggest_teams(
    members: list[dict[str, Any]],
    size: int,
    attempts: int = 3,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """Gợi ý các đội `size` người từ danh sách members (mỗi member có key 'zodiac').

    Trả về list [{members, score}] xếp theo điểm giảm dần (tối đa `attempts` phương án).
    """
    if len(members) < size:
        return []

    rng = rng or random.Random()
    teams = []

    for _ in range(attempts):
        shuffled = members[:]
        rng.shuffle(shuffled)
        team = shuffled[:size]

        total = 0
        count = 0
        for a in range(len(team)):
            for b in range(a + 1, len(team)):
                total += pair_score(team[a]["zodiac"]["dia_chi"], team[b]["zodiac"]["dia_chi"])
                count += 1

        teams.append({"members": team, "score": round(total / (count or 1))})

    teams.sort(key=lambda t: t["score"], reverse=True)
    return teams
