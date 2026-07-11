# Vận trình ngày/tháng — tính offline (Can Chi + cung) rồi Claude diễn giải chi tiết.
# Không có ANTHROPIC_API_KEY → trả phần "dữ kiện" (template) để vẫn hiển thị được.
# Bổ sung: cào lichngaytot.com theo yêu cầu (best-effort, gọi khi người dùng bấm nút).

import hashlib
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


def _strip_html(html: str, article_only: bool = True) -> str:
    m = re.search(r"(?is)<article[^>]*>(.*?)</article>", html)
    raw = m.group(1) if (article_only and m) else html
    raw = re.sub(r"(?is)<(script|style|nav|footer|header|form)[^>]*>.*?</\1>", " ", raw)
    txt = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"[ \t]*\n[ \t]*", "\n", re.sub(r"[^\S\n]+", " ", txt)).strip()


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
            result["day"] = {"url": url, "excerpt": _strip_html(r.text)[:3500]}
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
                idx = full.find(f"tuổi {dia_chi}")
                seg = full[idx : idx + 1800] if idx >= 0 else full[:2600]
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
                result["horoscope_day"] = {"url": url, "excerpt": _strip_html(r.text)[:2600]}
        except Exception:  # noqa: BLE001
            pass

    return result
