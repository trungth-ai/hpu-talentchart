# Test vận trình (đơn vị) — môi trường test không có ANTHROPIC_API_KEY nên fallback template.

import asyncio

from app.services.epa.fortune import fortune_narrative


def test_fortune_fallback_without_key():
    facts = "Hôm nay ngày Giáp Tý. Nhân sự tuổi Hợi, cung Ma Kết."
    out = asyncio.run(fortune_narrative("day", facts))
    assert out == facts  # không có key -> trả nguyên dữ kiện

    out_m = asyncio.run(fortune_narrative("month", facts))
    assert out_m == facts
