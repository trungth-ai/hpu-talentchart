# Response envelope helpers — BẮT BUỘC dùng cho mọi endpoint (rules/api-response.md)

from typing import Any


def success(data: Any, message: str = "Thành công", meta: dict | None = None) -> dict:
    """Envelope thành công: {status, data, message[, meta]}."""
    response: dict[str, Any] = {"status": "success", "data": data, "message": message}
    if meta:
        response["meta"] = meta
    return response


def error(message: str, code: str = "ERROR", errors: list | None = None) -> dict:
    """Envelope lỗi: {status, message, code, errors}."""
    return {"status": "error", "message": message, "code": code, "errors": errors or []}


def paginated(data: Any, page: int, per_page: int, total: int) -> dict:
    """Envelope danh sách có phân trang."""
    return success(
        data,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
    )
