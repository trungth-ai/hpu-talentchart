# Làm sạch nội dung tử vi tra cứu (astrology_reference) — cắt bỏ bảng OCR RÁC ở cuối:
#   "Thuộc tướng và tĩnh tọa / Số TT  Ngày tháng  Sao ... Sơn Dương ..." — bảng liệt kê 12 cung
#   hoàng đạo bị OCR sai, khó đọc, KHÔNG đúng (Trung yêu cầu bỏ khi hiển thị — xem ảnh).
# CHỈ cắt đúng bảng này; GIỮ nguyên phần "vận mệnh/thuộc tướng" và các đoạn "sinh tháng ..."
# (vận trình theo tháng sinh — nội dung hợp lệ, nằm TRƯỚC bảng rác). Regex nới lỏng chịu lỗi OCR.
# Dấu hiệu riêng của bảng rác: "và" đứng NGAY SAU "tướng" (khác "và thuộc tướng" ở đoạn hợp lệ).

import re

_CUT_PATTERNS = (
    r"[Tt]hu\S{0,3}c?\s+t\S*ng\s+v[àa]\s+[tl][ĩiìỉíậ]nh",  # header bảng rác ("tướng và tĩnh...")
    r"S[ốôổ0]?\s*TT\s+Ng[àa]y\s+th[áa]ng",                 # tiêu đề bảng: "Số TT Ngày tháng"
)
_CUT_RE = re.compile("|".join(f"(?:{p})" for p in _CUT_PATTERNS))


def clean_reference_text(text: str) -> str:
    """Cắt bỏ đuôi rác (nếu có) khỏi một đoạn text tử vi."""
    if not isinstance(text, str):
        return text
    m = _CUT_RE.search(text)
    return text[: m.start()].rstrip() if m else text


def clean_content(content):
    """Làm sạch đệ quy mọi chuỗi trong content (dict / list / str) của astrology_reference."""
    if isinstance(content, dict):
        return {k: clean_content(v) for k, v in content.items()}
    if isinstance(content, list):
        return [clean_content(v) for v in content]
    return clean_reference_text(content)
