# AuthMiddleware — decode JWT từ header Authorization, gắn payload vào request.state
# KHÔNG chặn request ở đây — việc bắt buộc đăng nhập do dependency get_current_user xử lý.
# Phải chạy TRƯỚC TenantMiddleware (tenant resolve org theo thứ tự JWT → subdomain → header dev).

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_token
from app.exceptions import UnauthorizedError


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.token_payload = None

        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
            try:
                request.state.token_payload = decode_token(token, expected_type="access")
            except UnauthorizedError:
                # Token hỏng/hết hạn: để payload = None, endpoint bảo vệ sẽ trả 401
                request.state.token_payload = None

        return await call_next(request)
