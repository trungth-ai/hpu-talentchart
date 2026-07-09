# Vận trình ngày/tháng — tính offline (Can Chi + cung) rồi Claude diễn giải chi tiết.
# Không có ANTHROPIC_API_KEY → trả phần "dữ kiện" (template) để vẫn hiển thị được.
# Bổ sung: cào lichngaytot.com theo yêu cầu (best-effort, gọi khi người dùng bấm nút).

import hashlib
import re

from app.config import get_settings

settings = get_settings()

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
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
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


async def scrape_lichngaytot(day: int, month: int, year: int) -> dict:
    """Cào best-effort trang xem ngày của lichngaytot.com (gọi theo yêu cầu người dùng).

    Trả {url, excerpt} nếu lấy được; raise ở router nếu lỗi. HTML site ngoài có thể đổi bất kỳ
    lúc nào nên đây là tính năng bổ trợ, không đảm bảo ổn định.
    """
    import httpx

    url = f"https://lichngaytot.com/lich-van-nien/xem-ngay-{day:02d}-{month:02d}-{year}.html"
    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (TalentChart EPA)"})
        resp.raise_for_status()
    html = resp.text
    # Bóc phần thân bài nếu có, rồi strip tag
    body = re.search(r"<article[^>]*>(.*?)</article>", html, re.S | re.I)
    raw = body.group(1) if body else html
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return {"url": url, "excerpt": text[:4000]}
