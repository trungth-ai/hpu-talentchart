# ★ Lịch âm — PORT NGUYÊN XI từ Fortune HR v6.2 (legacy/fortune-hr/server.js dòng 28-120)
# LunarData: bảng mã hoá lịch âm 1900-2099, mỗi phần tử 1 năm (bit 4-16: tháng đủ/thiếu,
# bit 0-3: tháng nhuận, bit 16: tháng nhuận đủ 30 ngày)

from datetime import date

# Bảng LunarData gốc — KHÔNG sửa bất kỳ hằng số nào
LUNAR_DATA = [
    0x04BD8, 0x04AE0, 0x0A570, 0x054D5, 0x0D260, 0x0D950, 0x16554, 0x056A0, 0x09AD0, 0x055D2,
    0x04AE0, 0x0A5B6, 0x0A4D0, 0x0D250, 0x1D255, 0x0B540, 0x0D6A0, 0x0ADA2, 0x095B0, 0x14977,
    0x04970, 0x0A4B0, 0x0B4B5, 0x06A50, 0x06D40, 0x1AB54, 0x02B60, 0x09570, 0x052F2, 0x04970,
    0x06566, 0x0D4A0, 0x0EA50, 0x06E95, 0x05AD0, 0x02B60, 0x186E3, 0x092E0, 0x1C8D7, 0x0C950,
    0x0D4A0, 0x1D8A6, 0x0B550, 0x056A0, 0x1A5B4, 0x025D0, 0x092D0, 0x0D2B2, 0x0A950, 0x0B557,
    0x06CA0, 0x0B550, 0x15355, 0x04DA0, 0x0A5D0, 0x14573, 0x052D0, 0x0A9A8, 0x0E950, 0x06AA0,
    0x0AEA6, 0x0AB50, 0x04B60, 0x0AAE4, 0x0A570, 0x05260, 0x0F263, 0x0D950, 0x05B57, 0x056A0,
    0x096D0, 0x04DD5, 0x04AD0, 0x0A4D0, 0x0D4D4, 0x0D250, 0x0D558, 0x0B540, 0x0B5A0, 0x195A6,
    0x095B0, 0x049B0, 0x0A974, 0x0A4B0, 0x0B27A, 0x06A50, 0x06D40, 0x0AF46, 0x0AB60, 0x09570,
    0x04AF5, 0x04970, 0x064B0, 0x074A3, 0x0EA50, 0x06B58, 0x055C0, 0x0AB60, 0x096D5, 0x092E0,
    0x0C960, 0x0D954, 0x0D4A0, 0x0DA50, 0x07552, 0x056A0, 0x0ABB7, 0x025D0, 0x092D0, 0x0CAB5,
    0x0A950, 0x0B4A0, 0x0BAA4, 0x0AD50, 0x055D9, 0x04BA0, 0x0A5B0, 0x15176, 0x052B0, 0x0A930,
    0x07954, 0x06AA0, 0x0AD50, 0x05B52, 0x04B60, 0x0A6E6, 0x0A4E0, 0x0D260, 0x0EA65, 0x0D530,
    0x05AA0, 0x076A3, 0x096D0, 0x04AFB, 0x04AD0, 0x0A4D0, 0x1D0B6, 0x0D250, 0x0D520, 0x0DD45,
    0x0B5A0, 0x056D0, 0x055B2, 0x049B0, 0x0A577, 0x0A4B0, 0x0AA50, 0x1B255, 0x06D20, 0x0ADA0,
    0x14B63, 0x09370, 0x049F8, 0x04970, 0x064B0, 0x168A6, 0x0EA50, 0x06B20, 0x1A6C4, 0x0AAE0,
    0x0A2E0, 0x0D2E3, 0x0C960, 0x0D557, 0x0D4A0, 0x0DA50, 0x05D55, 0x056A0, 0x0A6D0, 0x055D4,
    0x052D0, 0x0A9B8, 0x0A950, 0x0B4A0, 0x0B6A6, 0x0AD50, 0x055A0, 0x0ABA4, 0x0A5B0, 0x052B0,
    0x0B273, 0x06930, 0x07337, 0x06AA0, 0x0AD50, 0x14B55, 0x04B60, 0x0A570, 0x054E4, 0x0D160,
    0x0E968, 0x0D520, 0x0DAA0, 0x16AA6, 0x056D0, 0x04AE0, 0x0A9D4, 0x0A2D0, 0x0D150, 0x0F252,
]


def get_leap_month(year: int) -> int:
    """Tháng nhuận của năm âm (0 = không có)."""
    return LUNAR_DATA[year - 1900] & 0xF


def get_leap_days(year: int) -> int:
    """Số ngày của tháng nhuận (0 nếu không có tháng nhuận)."""
    if get_leap_month(year):
        return 30 if LUNAR_DATA[year - 1900] & 0x10000 else 29
    return 0


def get_lunar_year_days(year: int) -> int:
    """Tổng số ngày trong năm âm lịch."""
    total = 348
    mask = 0x8000
    while mask > 0x8:
        total += 1 if LUNAR_DATA[year - 1900] & mask else 0
        mask >>= 1
    return total + get_leap_days(year)


def get_lunar_month_days(year: int, month: int) -> int:
    """Số ngày của tháng âm (không tính nhuận): 29 hoặc 30."""
    return 30 if LUNAR_DATA[year - 1900] & (0x10000 >> month) else 29


def get_lunar_date(solar_year: int, solar_month: int, solar_day: int) -> dict:
    """Đổi dương lịch → âm lịch. Mốc: 31/01/1900 dương = 01/01/1900 âm.

    Ngoài phạm vi 1900-2100: trả nguyên ngày dương (theo hành vi bản gốc).
    """
    if solar_year < 1900 or solar_year > 2100:
        return {
            "lunar_year": solar_year,
            "lunar_month": solar_month,
            "lunar_day": solar_day,
        }

    offset = (date(solar_year, solar_month, solar_day) - date(1900, 1, 31)).days

    # Tìm năm âm
    lunar_year = 1900
    while lunar_year < 2100 and offset >= 0:
        days_in_year = get_lunar_year_days(lunar_year)
        if offset < days_in_year:
            break
        offset -= days_in_year
        lunar_year += 1

    # Tìm tháng âm (xử lý tháng nhuận đúng theo vòng lặp bản gốc)
    lunar_month = 1
    leap_month = get_leap_month(lunar_year)
    is_leap_month = False

    i = 1
    while i <= 12:
        if leap_month > 0 and i == leap_month + 1 and not is_leap_month:
            days_in_month = get_leap_days(lunar_year)
            is_leap_month = True
            i -= 1
        else:
            days_in_month = get_lunar_month_days(lunar_year, i)

        if offset < days_in_month:
            lunar_month = i
            break
        offset -= days_in_month
        i += 1

    return {
        "lunar_year": lunar_year,
        "lunar_month": lunar_month,
        "lunar_day": offset + 1,
        "is_leap_month": is_leap_month,
    }
