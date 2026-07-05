# Narrative EPA — Claude API polish (tùy chọn) với fallback template (ADR-005)
#
# Quy tắc (Critical Business Rules): AI CHỈ trau chuốt câu chữ dựa trên nội dung
# archetype có sẵn trong app/data/archetypes.py — không tự sáng tác nội dung mới.
# Cache 30 ngày để kiểm soát chi phí API (HUONG-DAN mục 10.4) — production dùng
# Redis; ở đây cache in-process, key theo hash input.

import hashlib

from app.config import get_settings

settings = get_settings()

# Cache in-process (production: thay bằng Redis TTL 30 ngày)
_cache: dict[str, str] = {}

_POLISH_PROMPT = (
    "Bạn là chuyên gia nhân sự. Hãy viết lại đoạn nhận xét tính cách sau đây cho "
    "mượt mà, chuyên nghiệp và ấm áp hơn (tiếng Việt, 1 đoạn văn, 120-180 từ). "
    "TUYỆT ĐỐI không thêm thông tin mới, không thay đổi ý nghĩa, không nhắc đến "
    "tử vi/phong thủy:\n\n{draft}"
)


async def polish_narrative(draft: str) -> str:
    """Trau chuốt narrative bằng Claude API nếu có key — lỗi/không có key → trả template."""
    if not settings.ANTHROPIC_API_KEY:
        return draft

    cache_key = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        # Import lazy — anthropic có thể chưa cài ở môi trường dev tối giản
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model="claude-sonnet-5",
            max_tokens=500,
            messages=[
                {"role": "user", "content": _POLISH_PROMPT.format(draft=draft)}
            ],
        )
        polished = response.content[0].text.strip()
        if polished:
            _cache[cache_key] = polished
            return polished
    except Exception:  # noqa: BLE001 — best-effort, mọi lỗi đều fallback template
        pass
    return draft
