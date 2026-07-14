# Celery config — background jobs + lịch chạy định kỳ (celery beat)
# Chạy: celery -A app.celery_app worker -Q default   /   celery -A app.celery_app beat

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "talentchart",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.fortune_tasks"],
)

celery_app.conf.update(
    task_default_queue="default",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    beat_schedule={
        # Cào tử vi theo KỲ, lưu fortune_content để hiển thị nhanh + xem lại (giảm cào/gọi AI).
        # Giờ VN. Kỳ thiếu lúc người dùng xem sẽ được cào bù (get_fortune).
        "scrape-fortune-day": {
            "task": "fortune.scrape",
            "schedule": crontab(hour=0, minute=15),
            "args": ("day",),
        },
        "scrape-fortune-week": {
            "task": "fortune.scrape",
            "schedule": crontab(hour=0, minute=30, day_of_week=1),  # thứ 2 hằng tuần
            "args": ("week",),
        },
        "scrape-fortune-month": {
            "task": "fortune.scrape",
            "schedule": crontab(hour=0, minute=45, day_of_month=1),  # mùng 1 hằng tháng
            "args": ("month",),
        },
        "scrape-fortune-year": {
            "task": "fortune.scrape",
            "schedule": crontab(hour=1, minute=0, day_of_month=1, month_of_year=1),  # 1/1
            "args": ("year",),
        },
    },
)
