# Đọc/ghi tử vi theo KỲ (bảng fortune_content): hiển thị nhanh từ DB + cào bù khi thiếu.
# Dùng bởi: router EPA (đọc theo kỳ, cào bù kỳ hiện tại) và Celery task (cào lô định kỳ).

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fortune_content import FortuneContent
from app.services.epa import fortune

PERIODS = ("day", "week", "month", "year")

# Chuẩn hoá kind từ scrape ngày (day/zodiac_day/horoscope_day) -> (day/zodiac/horoscope)
_DAY_KIND = {"day": "day", "zodiac_day": "zodiac", "horoscope_day": "horoscope"}


def period_key_for(period_type: str, on_date: date) -> str:
    """Khóa kỳ để tra/lưu: ngày→YYYY-MM-DD, tuần→YYYY-Www (ISO), tháng→YYYY-MM, năm→YYYY."""
    if period_type == "day":
        return on_date.isoformat()
    if period_type == "week":
        iso = on_date.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    if period_type == "month":
        return f"{on_date.year}-{on_date.month:02d}"
    if period_type == "year":
        return str(on_date.year)
    raise ValueError(f"period_type không hợp lệ: {period_type}")


def _keys_for(period_type: str, dia_chi: str, sign_code: str) -> dict[str, str]:
    """kind -> key cho 1 người ở 1 kỳ. Ngày có thêm 'day' (ngày tốt/xấu, chung, key='')."""
    keys = {"zodiac": dia_chi, "horoscope": sign_code}
    if period_type == "day":
        keys["day"] = ""
    return keys


async def _fetch(
    db: AsyncSession, period_type: str, pkey: str, keys: dict[str, str]
) -> dict[str, dict | None]:
    rows = await db.execute(
        select(FortuneContent)
        .where(FortuneContent.period_type == period_type)
        .where(FortuneContent.period_key == pkey)
    )
    index = {(r.kind, r.key): r for r in rows.scalars().all()}
    out: dict[str, dict | None] = {}
    for kind, key in keys.items():
        row = index.get((kind, key))
        out[kind] = {"url": row.source_url, "excerpt": row.excerpt} if row else None
    return out


async def _upsert(db: AsyncSession, period_type: str, pkey: str, records: list[dict]) -> None:
    for rec in records:
        obj = await db.get(FortuneContent, (period_type, pkey, rec["kind"], rec["key"]))
        if obj is None:
            obj = FortuneContent(
                period_type=period_type, period_key=pkey, kind=rec["kind"], key=rec["key"]
            )
            db.add(obj)
        obj.source_url = rec.get("url")
        obj.excerpt = rec.get("excerpt") or ""
        obj.scraped_at = datetime.now(UTC)


async def _scrape_batch(period_type: str, on_date: date) -> list[dict]:
    """Cào LÔ đủ 12 tuổi + 12 cung (cho cron). Ngày: thêm ngày tốt/xấu. Chuẩn hoá kind."""
    if period_type == "day":
        raw = await fortune.scrape_all_daily(on_date)
        return [{**r, "kind": _DAY_KIND.get(r["kind"], r["kind"])} for r in raw]
    return await fortune.scrape_period(period_type)


async def _lazy_scrape(period_type: str, today: date, dia_chi: str, sign_code: str) -> list[dict]:
    """Cào BÙ nhanh khi xem kỳ hiện tại mà DB thiếu. Ngày: chỉ cào cho đúng người (3 request);
    tuần/tháng/năm: cào cả 12 (bài gộp nên nhẹ)."""
    if period_type != "day":
        return await fortune.scrape_period(period_type)
    raw = await fortune.scrape_lichngaytot(dia_chi, sign_code, today)
    triples = (
        ("day", "day", ""),
        ("zodiac_day", "zodiac", dia_chi),
        ("horoscope_day", "horoscope", sign_code),
    )
    out: list[dict] = []
    for k_old, k_new, key in triples:
        blk = raw.get(k_old)
        if blk:
            out.append({"kind": k_new, "key": key, **blk})
    return out


async def scrape_and_store(db: AsyncSession, period_type: str, on_date: date) -> int:
    """Cào theo LÔ 1 kỳ (12 cung + 12 tuổi, +ngày tốt/xấu nếu là ngày) rồi lưu DB. Cho Celery."""
    pkey = period_key_for(period_type, on_date)
    records = await _scrape_batch(period_type, on_date)
    if records:
        await _upsert(db, period_type, pkey, records)
        await db.commit()
    return len(records)


async def get_fortune(
    db: AsyncSession,
    *,
    period_type: str,
    dia_chi: str,
    sign_code: str,
    on_date: date,
    today: date,
) -> dict:
    """Trả tử vi 1 kỳ cho 1 người, đọc từ DB. Nếu là kỳ HIỆN TẠI mà thiếu → cào bù rồi lưu.
    Kỳ quá khứ chỉ đọc (không cào lại)."""
    pkey = period_key_for(period_type, on_date)
    keys = _keys_for(period_type, dia_chi, sign_code)
    blocks = await _fetch(db, period_type, pkey, keys)

    is_current = pkey == period_key_for(period_type, today)
    if is_current and not all(blocks.values()):
        records = await _lazy_scrape(period_type, today, dia_chi, sign_code)
        if records:
            await _upsert(db, period_type, pkey, records)
            await db.commit()
            blocks = await _fetch(db, period_type, pkey, keys)

    return {"period_type": period_type, "period_key": pkey, **blocks}
