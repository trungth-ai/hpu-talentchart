# Nhịp sinh học (Biorhythm) — tính thuần toán từ ngày sinh.
# 3 chu kỳ kinh điển: Thể chất 23 ngày, Cảm xúc 28 ngày, Trí tuệ 33 ngày.
#   value(t) = sin(2π * số_ngày_đã_sống / chu_kỳ)  → chuẩn hóa về [-100, 100].
#
# LƯU Ý: chỉ là mô hình tham khảo, KHÔNG có giá trị y khoa/quyết định.

import math
from datetime import date

CYCLES = {"physical": 23, "emotional": 28, "intellectual": 33}


def _value(days: int, period: int) -> int:
    return round(math.sin(2 * math.pi * days / period) * 100)


def biorhythm_series(birth: date, center: date, span: int = 14) -> list[dict]:
    """Chuỗi giá trị 3 nhịp cho khoảng [center-span, center+span] ngày (vẽ biểu đồ)."""
    base = center.toordinal()
    series = []
    for off in range(-span, span + 1):
        d = date.fromordinal(base + off)
        days = (d - birth).days
        series.append(
            {
                "offset": off,
                "date": d.isoformat(),
                "physical": _value(days, 23),
                "emotional": _value(days, 28),
                "intellectual": _value(days, 33),
            }
        )
    return series


def biorhythm_today(birth: date, today: date) -> dict:
    """Giá trị 3 nhịp cho 1 ngày + số ngày đã sống."""
    days = (today - birth).days
    return {
        "days_alive": days,
        "physical": _value(days, 23),
        "emotional": _value(days, 28),
        "intellectual": _value(days, 33),
    }
