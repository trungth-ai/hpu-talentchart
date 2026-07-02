# Rule: API Response Envelope

## Quy tắc

**Mọi API endpoint PHẢI trả về JSON envelope `{status, data, message}`.**

## Pattern

### Success (đơn)
```json
{
  "status": "success",
  "data": { "id": 1, "full_name": "Nguyễn Văn A" },
  "message": "Thao tác thành công"
}
```

### Success (list có pagination)
```json
{
  "status": "success",
  "data": [...],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 98,
    "total_pages": 10
  }
}
```

### Error
```json
{
  "status": "error",
  "message": "Không tìm thấy nhân viên",
  "code": "NOT_FOUND",
  "errors": []
}
```

### Validation Error (422)
```json
{
  "status": "error",
  "message": "Dữ liệu không hợp lệ",
  "code": "VALIDATION_ERROR",
  "errors": [
    { "field": "email", "message": "Email không đúng định dạng" }
  ]
}
```

## Helper BẮT BUỘC dùng

```python
# src/core/responses.py

def success(data, message="Thành công", meta=None):
    response = {"status": "success", "data": data, "message": message}
    if meta:
        response["meta"] = meta
    return response

def error(message, code="ERROR", errors=None):
    return {"status": "error", "message": message, "code": code, "errors": errors or []}

def paginated(data, page, per_page, total):
    return success(data, meta={
        "page": page, "per_page": per_page, "total": total,
        "total_pages": (total + per_page - 1) // per_page
    })
```

## Anti-patterns

```python
# ❌ SAI — return model trực tiếp
@router.get("/{id}")
async def get(id: int):
    return db.query(Model).get(id)  # Không có envelope

# ❌ SAI — return dict không theo envelope
@router.get("/{id}")
async def get(id: int):
    return {"item": data}  # Sai format

# ✅ ĐÚNG
@router.get("/{id}")
async def get(id: int):
    item = db.query(Model).get(id)
    if not item:
        raise HTTPException(404, "Không tìm thấy")
    return success(ItemResponse.model_validate(item))
```

## Error codes chuẩn

| Code | HTTP | Khi nào |
|---|---|---|
| `NOT_FOUND` | 404 | Resource không tồn tại |
| `VALIDATION_ERROR` | 422 | Pydantic validation fail |
| `BUSINESS_RULE_ERROR` | 422 | Vi phạm rule nghiệp vụ |
| `DUPLICATE` | 409 | Trùng unique constraint |
| `FORBIDDEN` | 403 | Không có quyền (chỉ system permissions, KHÔNG tenant) |
| `UNAUTHORIZED` | 401 | Chưa đăng nhập |
| `RATE_LIMIT` | 429 | Quá rate limit |
| `INTERNAL_ERROR` | 500 | Lỗi server |

## Lý do

- Frontend xử lý response thống nhất (luôn check `status === "success"`)
- Error handling tập trung
- Mở rộng meta dễ (thêm pagination, debug info)
- Dễ debug: luôn có `message` và `code`

## Vi phạm = block merge

Endpoint không dùng envelope sẽ bị từ chối ở review.
