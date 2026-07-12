# Vận trình ngày/tháng — tính offline (Can Chi + cung) rồi Claude diễn giải chi tiết.
# Không có ANTHROPIC_API_KEY → trả phần "dữ kiện" (template) để vẫn hiển thị được.
# Bổ sung: cào lichngaytot.com theo yêu cầu (best-effort, gọi khi người dùng bấm nút).

import hashlib
import html
import re
from datetime import date

from app.config import get_settings

settings = get_settings()

LNT_BASE = "https://lichngaytot.com"
_LNT_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9",
}
# code cung -> slug trang tử vi ngày của lichngaytot (/cung-hoang-dao/{slug}.html)
CUNG_SLUG = {
    "ARIES": "bach-duong-1",
    "TAURUS": "kim-nguu-2",
    "GEMINI": "song-tu-3",
    "CANCER": "cu-giai-4",
    "LEO": "su-tu-5",
    "VIRGO": "xu-nu-6",
    "LIBRA": "thien-binh-7",
    "SCORPIO": "ho-cap-8",
    "SAGITTARIUS": "nhan-ma-9",
    "CAPRICORN": "ma-ket-10",
    "AQUARIUS": "bao-binh-11",
    "PISCES": "song-ngu-12",
}

# Cache in-process theo (kind|facts) — production nên thay bằng Redis TTL ngày.
_cache: dict[str, str] = {}


async def fortune_narrative(kind: str, facts: str) -> str:
    """kind='day'|'month'. Claude sinh nhận định vận trình từ dữ kiện; lỗi/không key → template."""
    if not settings.ANTHROPIC_API_KEY:
        return facts
    cache_key = hashlib.sha256(f"{kind}|{facts}".encode()).hexdigest()
    if cache_key in _cache:
        return _cache[cache_key]
    try:
        from anthropic import AsyncAnthropic

        period = "NGÀY HÔM NAY" if kind == "day" else "THÁNG NÀY"
        prompt = (
            "Bạn là chuyên gia tư vấn theo tử vi phương Đông và chiêm tinh phương Tây. "
            f"Dựa DUY NHẤT trên dữ kiện dưới đây, viết một đoạn nhận định vận trình {period} "
            "cho nhân sự (tiếng Việt, ấm áp, tích cực, chi tiết, 160-240 từ), gồm: tổng quan, "
            "công việc, sức khỏe/tinh thần và 1-2 lời khuyên hành động. Không bịa số liệu, "
            "kết đoạn nhắc đây chỉ là thông tin tham khảo.\n\nDỮ KIỆN:\n" + facts
        )
        # timeout + max_retries ngắn: nếu Claude chậm/không tới được thì fail-fast → template
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY, timeout=18.0, max_retries=1)
        resp = await client.messages.create(
            model="claude-sonnet-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        if text:
            _cache[cache_key] = text
            return text
    except Exception:  # noqa: BLE001 — best-effort, mọi lỗi đều fallback template
        pass
    return facts


# Thẻ khối -> ngắt dòng (giữ bố cục đoạn, tránh dồn thành 1 khối chữ khó đọc)
_BLOCK_TAG_RE = re.compile(
    r"(?is)</(p|div|li|tr|h[1-6]|section|article|blockquote)>|<br\s*/?>|</td>"
)
# 12 địa chi — dùng để cắt đúng đoạn của từng con giáp trong bài "tử vi theo tuổi"
_DIA_CHI = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")


def _strip_html(raw_html: str, article_only: bool = True) -> str:
    """Bóc HTML về text sạch: giữ ngắt đoạn, decode entity (&#237; -> í), gom khoảng trắng."""
    m = re.search(r"(?is)<article[^>]*>(.*?)</article>", raw_html)
    raw = m.group(1) if (article_only and m) else raw_html
    # Bỏ hẳn khối không phải nội dung
    raw = re.sub(r"(?is)<(script|style|nav|footer|header|form)[^>]*>.*?</\1>", " ", raw)
    # Thẻ khối -> newline TRƯỚC khi xoá mọi thẻ, để giữ ranh giới đoạn
    raw = _BLOCK_TAG_RE.sub("\n", raw)
    txt = re.sub(r"<[^>]+>", " ", raw)
    # GỐC LỖI "B&#237;nh": decode HTML entity (&#237; -> í, &amp; -> &, &nbsp; -> \xa0...)
    txt = html.unescape(txt).replace("\xa0", " ")
    # Gom khoảng trắng trong dòng; gộp tối đa 1 dòng trống giữa các đoạn
    txt = re.sub(r"[^\S\n]+", " ", txt)
    txt = re.sub(r" *\n *", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def _extract_age_segment(full: str, dia_chi: str) -> str:
    """Cắt đúng đoạn 1 con giáp: từ 'tuổi {chi}' tới 'tuổi {chi kế}' (không cắt cụt giữa chừng)."""
    lower = full.lower()
    start = lower.find(f"tuổi {dia_chi.lower()}")
    if start < 0:
        return full[:2800]
    end = len(full)
    for chi in _DIA_CHI:
        if chi == dia_chi:
            continue
        pos = lower.find(f"tuổi {chi.lower()}", start + 1)
        if 0 <= pos < end:
            end = pos
    return full[start:end].strip()[:4000]


async def scrape_lichngaytot(dia_chi: str, sign_code: str, today: date) -> dict:
    """Cào 3 nội dung từ lichngaytot.com (gọi theo yêu cầu người dùng — best-effort).

    1. Ngày tốt/xấu, sao, giờ hoàng đạo: /xem-ngay-tot-xau-DD-MM-YYYY
    2. Tử vi ngày theo tuổi: tìm bài "tu-vi-hang-ngay-D-M-YYYY" trên /tu-vi.html,
       cắt đoạn của con giáp
    3. Tử vi ngày theo cung: /cung-hoang-dao/{slug}.html
    Mỗi phần độc lập, lỗi phần nào thì phần đó = None (trang ngoài có thể đổi bất kỳ lúc nào).
    """
    import httpx

    result: dict = {"day": None, "zodiac_day": None, "horoscope_day": None}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=_LNT_UA) as client:
        # 1) Ngày tốt/xấu
        try:
            url = f"{LNT_BASE}/xem-ngay-tot-xau-{today.day:02d}-{today.month:02d}-{today.year}"
            r = await client.get(url)
            r.raise_for_status()
            result["day"] = {"url": url, "excerpt": _strip_html(r.text)[:6000]}
        except Exception:  # noqa: BLE001
            pass

        # 2) Tử vi ngày theo tuổi (crawl hub -> bài trong ngày -> cắt đoạn con giáp)
        try:
            hub = await client.get(f"{LNT_BASE}/tu-vi.html")
            hub.raise_for_status()
            m = re.search(
                rf"(tu-vi-hang-ngay-{today.day}-{today.month}-{today.year}-[0-9-]+\.html)",
                hub.text,
            )
            if m:
                art_url = f"{LNT_BASE}/tu-vi/{m.group(1)}"
                ra = await client.get(art_url)
                ra.raise_for_status()
                full = _strip_html(ra.text)
                seg = _extract_age_segment(full, dia_chi)
                result["zodiac_day"] = {"url": art_url, "excerpt": seg}
        except Exception:  # noqa: BLE001
            pass

        # 3) Tử vi ngày theo cung hoàng đạo
        try:
            slug = CUNG_SLUG.get(sign_code)
            if slug:
                url = f"{LNT_BASE}/cung-hoang-dao/{slug}.html"
                r = await client.get(url)
                r.raise_for_status()
                result["horoscope_day"] = {"url": url, "excerpt": _strip_html(r.text)[:4000]}
        except Exception:  # noqa: BLE001
            pass

    return result


async def scrape_all_daily(today: date) -> list[dict]:
    """Cào theo LÔ cho cron: ngày tốt/xấu (1 trang) + tử vi theo tuổi cả 12 con giáp (1 bài,
    cắt theo từng địa chi) + tử vi theo cung cả 12 cung (12 trang).

    Trả list record {kind, key, url, excerpt} để lưu vào bảng daily_fortunes.
    Best-effort — phần nào lỗi thì bỏ phần đó (trang ngoài đổi bất kỳ lúc nào).
    """
    import httpx

    records: list[dict] = []
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers=_LNT_UA) as client:
        # 1) Ngày tốt/xấu — chung mọi người (kind='day', key='')
        try:
            url = f"{LNT_BASE}/xem-ngay-tot-xau-{today.day:02d}-{today.month:02d}-{today.year}"
            r = await client.get(url)
            r.raise_for_status()
            records.append(
                {"kind": "day", "key": "", "url": url, "excerpt": _strip_html(r.text)[:6000]}
            )
        except Exception:  # noqa: BLE001
            pass

        # 2) Tử vi ngày theo tuổi — 1 bài chứa CẢ 12 con giáp, cắt theo từng địa chi
        try:
            hub = await client.get(f"{LNT_BASE}/tu-vi.html")
            hub.raise_for_status()
            m = re.search(
                rf"(tu-vi-hang-ngay-{today.day}-{today.month}-{today.year}-[0-9-]+\.html)",
                hub.text,
            )
            if m:
                art_url = f"{LNT_BASE}/tu-vi/{m.group(1)}"
                ra = await client.get(art_url)
                ra.raise_for_status()
                full = _strip_html(ra.text)
                for chi in _DIA_CHI:
                    seg = _extract_age_segment(full, chi)
                    # chỉ lưu khi thực sự tìm thấy đoạn của con giáp này (tránh fallback nhầm)
                    if f"tuổi {chi.lower()}" in seg.lower():
                        records.append(
                            {"kind": "zodiac_day", "key": chi, "url": art_url, "excerpt": seg}
                        )
        except Exception:  # noqa: BLE001
            pass

        # 3) Tử vi ngày theo cung — cả 12 cung hoàng đạo
        for code, slug in CUNG_SLUG.items():
            try:
                url = f"{LNT_BASE}/cung-hoang-dao/{slug}.html"
                r = await client.get(url)
                r.raise_for_status()
                records.append(
                    {
                        "kind": "horoscope_day",
                        "key": code,
                        "url": url,
                        "excerpt": _strip_html(r.text)[:4000],
                    }
                )
            except Exception:  # noqa: BLE001
                continue

    return records
