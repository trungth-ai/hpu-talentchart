# Custom exceptions — map sang error envelope chuẩn (rules/api-response.md)
# Handler đăng ký trong main.py


class AppException(Exception):
    """Exception gốc của app — luôn trả envelope {status, message, code, errors}."""

    def __init__(
        self,
        message: str,
        code: str = "ERROR",
        http_status: int = 400,
        errors: list | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.http_status = http_status
        self.errors = errors or []
        super().__init__(message)


class ResourceNotFound(AppException):
    """404 — dùng CẢ cho cross-tenant access (trả 404, KHÔNG 403 — tránh leak existence)."""

    def __init__(self, resource: str = "Tài nguyên") -> None:
        super().__init__(
            message=f"Không tìm thấy {resource}", code="NOT_FOUND", http_status=404
        )


class DuplicateResource(AppException):
    """409 — trùng unique constraint."""

    def __init__(self, message: str = "Dữ liệu đã tồn tại") -> None:
        super().__init__(message=message, code="DUPLICATE", http_status=409)


class UnauthorizedError(AppException):
    """401 — chưa đăng nhập hoặc token không hợp lệ."""

    def __init__(self, message: str = "Chưa đăng nhập hoặc phiên đã hết hạn") -> None:
        super().__init__(message=message, code="UNAUTHORIZED", http_status=401)


class ForbiddenError(AppException):
    """403 — CHỈ dùng cho system permissions (VD: thiếu role), KHÔNG dùng cho cross-tenant."""

    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này") -> None:
        super().__init__(message=message, code="FORBIDDEN", http_status=403)


class BusinessRuleError(AppException):
    """422 — vi phạm rule nghiệp vụ."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, code="BUSINESS_RULE_ERROR", http_status=422)
