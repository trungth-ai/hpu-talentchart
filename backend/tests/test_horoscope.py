# Test tra cung hoàng đạo theo ngày sinh (đơn vị, không cần DB)

from datetime import date

import pytest

from app.data.horoscope import HOROSCOPE_SIGNS, get_sign_by_date


@pytest.mark.parametrize(
    "month,day,expected",
    [
        (3, 21, "Bạch Dương"),  # mốc đầu Bạch Dương
        (4, 19, "Bạch Dương"),  # mốc cuối Bạch Dương
        (4, 20, "Kim Ngưu"),    # sang Kim Ngưu
        (1, 1, "Ma Kết"),       # đầu năm vẫn Ma Kết (vắt qua năm)
        (1, 19, "Ma Kết"),
        (1, 20, "Bảo Bình"),
        (2, 18, "Bảo Bình"),
        (2, 19, "Song Ngư"),
        (6, 21, "Song Tử"),
        (6, 22, "Cự Giải"),
        (9, 23, "Thiên Bình"),
        (10, 23, "Thiên Bình"),
        (10, 24, "Bọ Cạp"),
        (11, 21, "Bọ Cạp"),
        (11, 22, "Nhân Mã"),
        (12, 21, "Nhân Mã"),
        (12, 22, "Ma Kết"),
        (12, 31, "Ma Kết"),
    ],
)
def test_get_sign_by_date(month: int, day: int, expected: str):
    assert get_sign_by_date(date(2000, month, day))["name"] == expected


def test_all_signs_have_required_fields():
    assert len(HOROSCOPE_SIGNS) == 12
    for s in HOROSCOPE_SIGNS:
        for field in ("name", "date_range", "element", "lucky_colors", "personality",
                      "strengths", "weaknesses", "careers"):
            assert s.get(field), f"{s['code']} thiếu {field}"
