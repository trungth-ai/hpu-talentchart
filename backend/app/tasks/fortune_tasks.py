# Celery task: cào tử vi theo KỲ (day/week/month/year) rồi lưu bảng fortune_content.
# Chạy định kỳ qua celery beat (xem celery_app.beat_schedule). KHÔNG cần tenant context —
# fortune_content là dữ liệu toàn cục (dùng chung mọi tổ chức).

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.celery_app import celery_app
from app.config import get_settings
from app.services.epa import fortune_content_store


async def _run(period_type: str, on_date: date) -> int:
    # Engine RIÊNG cho mỗi lần chạy task (không dùng chung engine async của web app —
    # kết nối asyncpg gắn event loop khác sẽ lỗi khi asyncio.run tạo loop mới).
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            return await fortune_content_store.scrape_and_store(session, period_type, on_date)
    finally:
        await engine.dispose()


@celery_app.task(name="fortune.scrape")
def scrape_fortune_task(period_type: str = "day", date_iso: str | None = None) -> int:
    """Cào + lưu tử vi 1 kỳ (mặc định hôm nay giờ VN). Trả số record đã lưu."""
    on_date = (
        date.fromisoformat(date_iso)
        if date_iso
        else datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()
    )
    return asyncio.run(_run(period_type, on_date))
