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
        # Cào tử vi hằng ngày lúc 00:15 giờ VN — lưu đủ 12 cung + 12 tuổi + ngày tốt/xấu vào DB
        # để hiển thị nhanh và cho phép xem lại các ngày trước (giảm cào/gọi AI lúc người dùng xem).
        "scrape-daily-fortune": {
            "task": "fortune.scrape_daily",
            "schedule": crontab(hour=0, minute=15),
        },
    },
)
