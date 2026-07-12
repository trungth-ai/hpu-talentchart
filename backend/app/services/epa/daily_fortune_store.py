# Đọc/ghi tử vi theo ngày (bảng daily_fortunes): hiển thị nhanh từ DB + cào bù khi thiếu.
# Dùng bởi: router EPA (đọc theo ngày, cào bù hôm nay) và Celery task (cào lô hằng ngày).

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_fortune import DailyFortune
from app.services.epa import fortune

# 3 loại nội dung tử vi theo ngày
_KINDS = ("day", "zodiac_day", "horoscope_day")


def _keys_for(dia_chi: str, sign_code: str) -> dict[str, str]:
    """Key mỗi kind cho 1 người: day→''; zodiac_day→địa chi; horoscope_day→code cung."""
    return {"day": "", "zodiac_day": dia_chi, "horoscope_day": sign_code}


async def _fetch_blocks(
    db: AsyncSession, on_date: date, keys: dict[str, str]
) -> dict[str, dict | None]:
    """Đọc từ DB các block tử vi của 1 ngày cho đúng 1 người (theo keys)."""
    rows = await db.execute(select(DailyFortune).where(DailyFortune.fortune_date == on_date))
    index = {(r.kind, r.key): r for r in rows.scalars().all()}
    out: dict[str, dict | None] = {}
    for kind in _KINDS:
        row = index.get((kind, keys[kind]))
        out[kind] = {"url": row.source_url, "excerpt": row.excerpt} if row else None
    return out


async def _upsert(db: AsyncSession, on_date: date, records: list[dict]) -> None:
    """Ghi/cập nhật các record {kind, key, url, excerpt} cho 1 ngày (idempotent theo PK)."""
    for rec in records:
        obj = await db.get(DailyFortune, (on_date, rec["kind"], rec["key"]))
        if obj is None:
            obj = DailyFortune(fortune_date=on_date, kind=rec["kind"], key=rec["key"])
            db.add(obj)
        obj.source_url = rec.get("url")
        obj.excerpt = rec.get("excerpt") or ""
        obj.scraped_at = datetime.now(UTC)


async def get_daily_for(
    db: AsyncSession, *, dia_chi: str, sign_code: str, on_date: date, today: date
) -> dict:
    """Trả tử vi 1 ngày cho 1 người, đọc từ DB. Nếu là HÔM NAY mà còn thiếu → cào bù (nhanh)
    rồi lưu DB. Ngày quá khứ không cào lại (chỉ đọc những gì đã lưu)."""
    keys = _keys_for(dia_chi, sign_code)
    blocks = await _fetch_blocks(db, on_date, keys)

    if on_date == today and not all(blocks.values()):
        scraped = await fortune.scrape_lichngaytot(dia_chi, sign_code, today)
        records: list[dict] = []
        if scraped.get("day"):
            records.append({"kind": "day", "key": "", **scraped["day"]})
        if scraped.get("zodiac_day"):
            records.append({"kind": "zodiac_day", "key": dia_chi, **scraped["zodiac_day"]})
        if scraped.get("horoscope_day"):
            records.append({"kind": "horoscope_day", "key": sign_code, **scraped["horoscope_day"]})
        if records:
            await _upsert(db, today, records)
            await db.commit()
            blocks = await _fetch_blocks(db, on_date, keys)

    return {"date": on_date.isoformat(), **blocks}


async def scrape_and_store_all(db: AsyncSession, today: date) -> int:
    """Cào theo LÔ đủ 12 cung + 12 tuổi + ngày tốt/xấu rồi lưu DB (dùng cho Celery cron).
    Trả số record đã lưu."""
    records = await fortune.scrape_all_daily(today)
    if records:
        await _upsert(db, today, records)
        await db.commit()
    return len(records)
