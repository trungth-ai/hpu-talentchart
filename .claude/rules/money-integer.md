# Rule: Money là Integer VNĐ

## Quy tắc

**Mọi giá trị tiền tệ (VNĐ) phải lưu là Integer, KHÔNG Float/Decimal.**

## Lý do

- VNĐ không có cents (phần thập phân)
- Float gây lỗi rounding: `0.1 + 0.2 = 0.30000000000000004`
- Decimal nặng hơn Integer ~5x
- Integer match với SQLite/PostgreSQL int8 — đủ lưu đến 9.2 quintillion VNĐ

## Pattern Database

```python
# ✅ ĐÚNG
base_salary = Column(Integer, default=0, nullable=False)  # 15000000

# ❌ SAI — Float
base_salary = Column(Float)  # 15000000.000000001

# ❌ SAI — Decimal (overkill cho VNĐ)
base_salary = Column(Numeric(15, 2))
```

## Pattern Pydantic

```python
# ✅ ĐÚNG
class EmployeeCreate(BaseModel):
    base_salary: int = 0  # int, không float

    @field_validator("base_salary")
    @classmethod
    def must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Lương phải >= 0")
        return v
```

## Format hiển thị

### Backend (Python/Jinja2)
```python
@app.template_filter('vnd')
def format_vnd(value):
    if value is None:
        return "0 đ"
    return f"{value:,.0f}".replace(",", ".") + " đ"

# Usage trong template: {{ employee.base_salary | vnd }}
# 15000000 → "15.000.000 đ"
```

### Frontend (JavaScript/Next.js)
```typescript
// lib/utils.ts
export function formatVND(amount: number): string {
    return new Intl.NumberFormat('vi-VN').format(amount) + ' đ';
}
// formatVND(15000000) → "15.000.000 đ"
```

## Phép tính tiền

```python
# ✅ ĐÚNG — Integer arithmetic
total = price * quantity              # int × int = int
tax = int(amount * 0.1)               # cast về int sau %
discount_amount = (total * 15) // 100 # integer division

# ❌ SAI — Float trong tính toán
tax = amount * 0.1  # → float, sai loại
```

## Phần trăm và tỷ lệ

```python
# Lưu phần trăm bằng Integer (×100 hoặc ×10000)
discount_percent = Column(Integer, default=0)  # 1500 = 15.00%
tax_rate = Column(Integer, default=1000)       # 1000 = 10.00%

# Tính:
amount_after_discount = amount - (amount * discount_percent // 10000)
```

## Excel Export

```python
# openpyxl format
ws['C5'] = 15000000
ws['C5'].number_format = '#,##0 "đ"'
# Hiển thị: 15,000,000 đ
```

## Edge cases

- Tỷ giá ngoại tệ: lưu rate × 10000 (4 decimal places)
  - VD: 1 USD = 24,500 VND → lưu là `245000000` (24500 × 10000)
- Phí dịch vụ %: lưu × 100
  - VD: 8.5% BHXH → lưu là `850`

## Vi phạm = block merge

Bất kỳ field nào liên quan tiền dùng Float/Decimal sẽ bị code review từ chối.
