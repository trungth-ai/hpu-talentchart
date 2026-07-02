# Celery config — background jobs (parse CV, sinh PDF...) sẽ thêm ở các sprint sau
# Sprint 1 chỉ cần file này tồn tại để docker-compose worker/beat khởi động được

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "talentchart",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_default_queue="default",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
)
