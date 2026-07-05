# ★ Can Chi / Nạp Âm / Mệnh — PORT NGUYÊN XI từ Fortune HR v6.2 (server.js dòng 122-222)
#
# QUY TẮC SỐNG CÒN: tính Can Chi theo NĂM ÂM LỊCH, không phải năm dương —
# sinh trước Tết phải tính theo năm âm trước đó.
# Test bắt buộc: get_canchi_from_birth(1, 1, 1938) == "Đinh Sửu" (KHÔNG phải Mậu Dần).

from datetime import date

from app.services.epa.lunar import get_lunar_date

THIEN_CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
DIA_CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]
CON_GIAP = ["Chuột", "Trâu", "Hổ", "Mèo", "Rồng", "Rắn", "Ngựa", "Dê", "Khỉ", "Gà", "Chó", "Lợn"]
EMOJI_GIAP = ["🐭", "🐮", "🐯", "🐱", "🐲", "🐍", "🐴", "🐐", "🐵", "🐔", "🐶", "🐷"]

NAP_AM = [
    "Hải Trung Kim", "Hải Trung Kim", "Lư Trung Hỏa", "Lư Trung Hỏa",
    "Đại Lâm Mộc", "Đại Lâm Mộc", "Lộ Bàng Thổ", "Lộ Bàng Thổ",
    "Kiếm Phong Kim", "Kiếm Phong Kim", "Sơn Đầu Hỏa", "Sơn Đầu Hỏa",
    "Giản Hạ Thủy", "Giản Hạ Thủy", "Thành Đầu Thổ", "Thành Đầu Thổ",
    "Bạch Lạp Kim", "Bạch Lạp Kim", "Dương Liễu Mộc", "Dương Liễu Mộc",
    "Tuyền Trung Thủy", "Tuyền Trung Thủy", "Ốc Thượng Thổ", "Ốc Thượng Thổ",
    "Tích Lịch Hỏa", "Tích Lịch Hỏa", "Tùng Bách Mộc", "Tùng Bách Mộc",
    "Trường Lưu Thủy", "Trường Lưu Thủy", "Sa Trung Kim", "Sa Trung Kim",
    "Sơn Hạ Hỏa", "Sơn Hạ Hỏa", "Bình Địa Mộc", "Bình Địa Mộc",
    "Bích Thượng Thổ", "Bích Thượng Thổ", "Kim Bạch Kim", "Kim Bạch Kim",
    "Phúc Đăng Hỏa", "Phúc Đăng Hỏa", "Thiên Hà Thủy", "Thiên Hà Thủy",
    "Đại Trạch Thổ", "Đại Trạch Thổ", "Thoa Xuyến Kim", "Thoa Xuyến Kim",
    "Tang Đố Mộc", "Tang Đố Mộc", "Đại Khê Thủy", "Đại Khê Thủy",
    "Sa Trung Thổ", "Sa Trung Thổ", "Thiên Thượng Hỏa", "Thiên Thượng Hỏa",
    "Thạch Lựu Mộc", "Thạch Lựu Mộc", "Đại Hải Thủy", "Đại Hải Thủy",
]

MENH_MAP = {
    "Kim": ["Hải Trung Kim", "Kiếm Phong Kim", "Bạch Lạp Kim", "Sa Trung Kim",
            "Kim Bạch Kim", "Thoa Xuyến Kim"],
    "Mộc": ["Đại Lâm Mộc", "Dương Liễu Mộc", "Tùng Bách Mộc", "Bình Địa Mộc",
            "Tang Đố Mộc", "Thạch Lựu Mộc"],
    "Thủy": ["Giản Hạ Thủy", "Tuyền Trung Thủy", "Trường Lưu Thủy", "Thiên Hà Thủy",
             "Đại Khê Thủy", "Đại Hải Thủy"],
    "Hỏa": ["Lư Trung Hỏa", "Sơn Đầu Hỏa", "Tích Lịch Hỏa", "Sơn Hạ Hỏa",
            "Phúc Đăng Hỏa", "Thiên Thượng Hỏa"],
    "Thổ": ["Lộ Bàng Thổ", "Thành Đầu Thổ", "Ốc Thượng Thổ", "Bích Thượng Thổ",
            "Đại Trạch Thổ", "Sa Trung Thổ"],
}


def get_canchi_from_birth(solar_day: int, solar_month: int, solar_year: int) -> dict:
    """Tính Can Chi/Nạp Âm/Mệnh từ ngày sinh DƯƠNG lịch (đổi sang năm ÂM trước khi tính)."""
    lunar = get_lunar_date(solar_year, solar_month, solar_day)
    lunar_year = lunar["lunar_year"]

    can_idx = (lunar_year - 4) % 10
    chi_idx = (lunar_year - 4) % 12
    nap_am_idx = (lunar_year - 4) % 60

    nap_am = NAP_AM[nap_am_idx]

    menh = "Thổ"
    for element, nap_am_list in MENH_MAP.items():
        if nap_am in nap_am_list:
            menh = element
            break

    return {
        "thien_can": THIEN_CAN[can_idx],
        "dia_chi": DIA_CHI[chi_idx],
        "con_giap": CON_GIAP[chi_idx],
        "emoji": EMOJI_GIAP[chi_idx],
        "tuoi_am": THIEN_CAN[can_idx] + " " + DIA_CHI[chi_idx],
        "nap_am": nap_am,
        "menh": menh,
        "lunar_year": lunar_year,
        "lunar_month": lunar["lunar_month"],
        "lunar_day": lunar["lunar_day"],
    }


def get_today_canchi(today: date | None = None) -> dict:
    """Can Chi hôm nay cho dashboard (port từ getTodayCanChi, server.js dòng 192-222)."""
    if today is None:
        today = date.today()

    lunar = get_lunar_date(today.year, today.month, today.day)

    year_can = THIEN_CAN[(lunar["lunar_year"] - 4) % 10]
    year_chi = DIA_CHI[(lunar["lunar_year"] - 4) % 12]

    # Can Chi ngày — mốc 07/01/2000 là ngày Giáp Tý (giữ nguyên bản gốc)
    diff = (today - date(2000, 1, 7)).days
    day_can = THIEN_CAN[((diff % 10) + 10) % 10]
    day_chi = DIA_CHI[((diff % 12) + 12) % 12]

    return {
        "solar_date": f"{today.day}/{today.month}/{today.year}",
        "lunar_date": f"{lunar['lunar_day']}/{lunar['lunar_month']}/{lunar['lunar_year']}",
        "lunar_year": lunar["lunar_year"],
        "lunar_month": lunar["lunar_month"],
        "lunar_day": lunar["lunar_day"],
        "year_canchi": year_can + " " + year_chi,
        "day_canchi": day_can + " " + day_chi,
    }
