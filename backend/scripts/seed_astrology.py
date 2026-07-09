# Nạp nội dung tử vi ĐẦY ĐỦ (con giáp + cung hoàng đạo) vào bảng astrology_reference.
# Nguồn: app/data/astrology_full.json (bóc nguyên văn từ tài liệu Trung cung cấp).
#
# Chạy trong container:  docker compose exec backend python scripts/seed_astrology.py
# Idempotent: chạy lại sẽ cập nhật (upsert) chứ không nhân đôi.

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.horoscope import HOROSCOPE_SIGNS  # noqa: E402
from app.data.zodiac_animals import ZODIAC_ANIMALS  # noqa: E402
from app.database import async_session_factory  # noqa: E402
from app.models.astrology import AstrologyReference  # noqa: E402

DATA_FILE = Path(__file__).resolve().parent.parent / "app" / "data" / "astrology_full.json"


async def seed() -> None:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    name_by_code = {s["code"]: s["name"] for s in HOROSCOPE_SIGNS}

    rows: list[tuple[str, str, str, dict]] = []
    # Con giáp
    for dia_chi, full in data.get("zodiac", {}).items():
        animal = ZODIAC_ANIMALS.get(dia_chi, {}).get("animal", dia_chi)
        rows.append(("zodiac", dia_chi, f"Tuổi {animal}", {"animal": animal, "full": full}))
    # Cung hoàng đạo — gộp nội dung từ cả 2 sách
    codes = set(data.get("book1", {})) | set(data.get("tuvitay", {}))
    for code in codes:
        rows.append(
            (
                "horoscope",
                code,
                name_by_code.get(code, code),
                {
                    "book1": data.get("book1", {}).get(code, ""),
                    "tuvitay": data.get("tuvitay", {}).get(code, ""),
                },
            )
        )
    # Tương hợp/tương xung 12 con giáp (EPA) — ma trận theo từng tuổi (địa chi X)
    for dia_chi, pairs in data.get("compat", {}).items():
        if pairs:
            animal = ZODIAC_ANIMALS.get(dia_chi, {}).get("animal", dia_chi)
            rows.append(("compat", dia_chi, f"Tương hợp tuổi {animal}", pairs))

    async with async_session_factory() as session:
        for kind, key, title, content in rows:
            obj = await session.get(AstrologyReference, (kind, key))
            if obj is not None:
                obj.title = title
                obj.content = content
            else:
                session.add(
                    AstrologyReference(kind=kind, key=key, title=title, content=content)
                )
        await session.commit()

    print(f"[OK] Da nap {len(rows)} dong astrology_reference "
          f"({sum(k=='zodiac' for k,_,_,_ in rows)} con giap, "
          f"{sum(k=='horoscope' for k,_,_,_ in rows)} cung hoang dao, "
          f"{sum(k=='compat' for k,_,_,_ in rows)} bang tuong hop)")


if __name__ == "__main__":
    asyncio.run(seed())
