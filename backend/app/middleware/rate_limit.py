# Rate limiting — slowapi
# Login: 5 request/phút/IP (PLAN.md Story 1). Storage: memory cho dev/test,
# production set RATE_LIMIT_STORAGE_URI=redis://... trong env.

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    default_limits=[],  # không giới hạn mặc định, chỉ limit endpoint gắn decorator
)

LOGIN_RATE_LIMIT = "5/minute"
