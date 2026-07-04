# Google OAuth — verify ID token qua Google tokeninfo (ADR-004)
# Frontend dùng Google Identity Services lấy id_token rồi gửi về backend.

import httpx

from app.config import get_settings
from app.exceptions import BusinessRuleError, UnauthorizedError

settings = get_settings()

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


async def verify_google_id_token(id_token: str) -> dict:
    """Verify id_token với Google, trả về claims (email, hd, name, sub...).

    Trong test, hàm này được monkeypatch — không gọi Google thật.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise BusinessRuleError(
            "Đăng nhập Google chưa được cấu hình trên hệ thống (thiếu GOOGLE_CLIENT_ID)"
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
    except httpx.HTTPError as exc:
        raise UnauthorizedError("Không xác thực được với Google, vui lòng thử lại") from exc

    if response.status_code != 200:
        raise UnauthorizedError("Token Google không hợp lệ hoặc đã hết hạn")

    claims = response.json()

    # aud phải đúng client id của app (chặn token cấp cho app khác)
    if claims.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise UnauthorizedError("Token Google không thuộc ứng dụng này")

    # Google trả email_verified dạng chuỗi "true"/"false"
    if str(claims.get("email_verified")).lower() != "true":
        raise UnauthorizedError("Email Google chưa được xác minh")

    if not claims.get("email"):
        raise UnauthorizedError("Token Google không chứa email")

    return claims


def extract_email_domain(email: str) -> str:
    """'user@hpu.edu.vn' → 'hpu.edu.vn'"""
    return email.rsplit("@", 1)[-1].lower()
