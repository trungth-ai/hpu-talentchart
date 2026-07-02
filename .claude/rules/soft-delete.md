# Rule: Soft Delete (mọi project)

## Quy tắc

**KHÔNG BAO GIỜ hard delete dữ liệu.** Luôn dùng soft delete bằng cách set `status = "inactive"`.

## Lý do

- Audit trail: vẫn có thể truy ngược thông tin đã xoá
- Recovery: khôi phục được khi user xoá nhầm
- Compliance: nhiều quy định pháp lý yêu cầu giữ data 5-10 năm
- Foreign key safety: tránh vỡ relationship khi xoá

## Pattern

```python
# ✅ ĐÚNG — Soft delete
@router.delete("/{id}")
async def delete_employee(id: int, db: Session = Depends(get_db)):
    item = db.query(Employee).filter(Employee.id == id).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy")
    item.status = "inactive"
    item.updated_at = datetime.now()
    db.commit()
    return success(None, "Đã xóa")


# ❌ SAI — Hard delete (CẤM)
db.delete(item)
db.commit()
```

## List query mặc định filter `status = "active"`

```python
# ✅ ĐÚNG — mặc định chỉ trả active
@router.get("")
async def list_employees(
    status: Optional[str] = "active",  # Default
    include_inactive: bool = False,    # Param riêng cho admin
    db: Session = Depends(get_db),
):
    query = db.query(Employee)
    if not include_inactive:
        query = query.filter(Employee.status == "active")
    # ...
```

## Restore (khôi phục)

Tạo endpoint riêng cho admin:
```python
@router.post("/{id}/restore")
@require_role("admin")
async def restore_employee(id: int, db: Session = Depends(get_db)):
    item = db.query(Employee).filter(Employee.id == id).first()
    if not item:
        raise HTTPException(404, "Không tìm thấy")
    item.status = "active"
    db.commit()
    return success(None, "Đã khôi phục")
```

## Hard delete chỉ trong các trường hợp ngoại lệ

- GDPR right-to-be-forgotten request (audit log + admin manual)
- Data > 7 năm (theo policy retention)
- Test data trong dev/staging

Trong code production, không có pattern hard delete.

## Status values chuẩn

- `active` — đang hoạt động (default)
- `inactive` — đã xóa / ngừng hoạt động
- Business-specific: `draft`, `pending`, `approved`, `rejected`...
