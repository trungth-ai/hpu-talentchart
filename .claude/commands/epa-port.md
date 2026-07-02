# /epa-port — Port logic JS (Fortune HR) → Python (TalentChart)

Áp dụng cho: TalentChart project (có folder `src/services/epa/`)

## Khi nào dùng

User chạy `/epa-port {module}` để port một module logic từ Fortune HR sang Python.

Ví dụ:
- `/epa-port lunar` → port LunarData + lunar conversion
- `/epa-port canchi` → port Can Chi calculation
- `/epa-port team-suggest` → port team chemistry algorithm

## Nguyên tắc

⚠️ **Port nguyên xi, KHÔNG cải tiến thuật toán.**
Code Fortune HR đã chạy production ổn định ở tuvi.hpu.edu.vn.
Chỉ:
- Đổi naming sang snake_case Python
- Thêm type hints + TypedDict
- Đổi sang async nếu có I/O
- Verify output Python = output JS bằng test cases

## Việc cần làm

### Step 1 — Đọc code JS gốc

```bash
# Code nằm tại đâu (đã extract khi setup project):
~/hpu-dev/talentchart/legacy/fortune-hr/backend/server.js
```

Đọc và hiểu logic của module được yêu cầu port. Đặc biệt chú ý:
- Constants (mảng, dictionary): copy nguyên xi giá trị
- Bug fix comments (// FIX:, // IMPORTANT:): GIỮ NGUYÊN
- Edge cases: liệt kê ra để test sau

### Step 2 — Tạo file Python tương ứng

Vị trí: `src/services/epa/{module}.py`

Template:
```python
# src/services/epa/{module}.py

"""
{Module description}.
Port từ Fortune HR (Express.js + better-sqlite3) sang Python.
KHÔNG sửa logic — đã được kiểm chứng production tại tuvi.hpu.edu.vn.
"""

from typing import TypedDict
from datetime import date


# ==== CONSTANTS (port nguyên xi từ JS) ====
# {Description}
{CONSTANT_NAME} = [
    # ... copy values từ JS
]


# ==== TYPED RESULT ====
class {ModuleName}Result(TypedDict):
    {field1}: {type1}
    # ...


# ==== CORE FUNCTIONS ====
def {function_name}(...) -> {ReturnType}:
    """
    {Docstring giải thích thuật toán}

    Args:
        ...

    Returns:
        ...

    Raises:
        ValueError: if input out of range
    """
    # ... logic port từ JS
    pass
```

### Step 3 — Tạo test cases verify output

Vị trí: `tests/services/epa/test_{module}.py`

```python
import pytest
from src.services.epa.{module} import {function}

# Test cases có expected output từ Fortune HR JS
TEST_CASES = [
    # (input, expected_output_from_js)
    ({...}, {...}),
    # ... ít nhất 20 test cases để cover các edge case
]

@pytest.mark.parametrize("input_data,expected", TEST_CASES)
def test_{function}_matches_fortune_hr(input_data, expected):
    result = {function}(**input_data)
    assert result == expected, f"Mismatch: {result} vs {expected}"
```

### Step 4 — Special case: port `lunar.py`

Nếu user yêu cầu port lunar:
1. Copy mảng `LUNAR_DATA` (200 entries) NGUYÊN XI
2. Port functions: `getLunarYearDays`, `getLeapMonth`, `getLeapDays`,
   `getLunarMonthDays`, `getLunarDate`
3. Test case BẮT BUỘC có:
   - Test bug fix Lunar Year cho người sinh trước Tết:
     `get_lunar_date(1938, 1, 1)` → `lunar_year == 1937`
   - Year 1900 (boundary)
   - Year 2100 (boundary)
   - Tháng nhuận năm 2023 (tháng 2 nhuận)

### Step 5 — Update __init__.py

```python
# src/services/epa/__init__.py
from .lunar import get_lunar_date, get_lunar_year_days
from .canchi import get_canchi_from_birth
# ... export các function vừa port
```

### Step 6 — Run tests

```bash
docker compose exec backend uv run pytest tests/services/epa/test_{module}.py -v
```

⚠️ Nếu test fail: KHÔNG sửa thuật toán Python. Đó là bug ở port (typo), KHÔNG phải bug ở logic gốc.

## Output cho user

```
✅ Port {module} hoàn thành

📁 Files đã tạo:
- src/services/epa/{module}.py
- tests/services/epa/test_{module}.py

🧪 Test results:
- {N} test cases pass
- Verified output matches Fortune HR JS

📝 Bước tiếp theo:
- Review code: `cat src/services/epa/{module}.py`
- Thêm endpoint API expose (nếu cần): /api/v1/epa/{...}
```

## Gotchas

- ⚠️ KHÔNG "cải tiến" thuật toán — port nguyên xi
- ⚠️ Bit operations: Python và JS có behavior tương tự, nhưng cẩn thận với signed/unsigned
- ⚠️ LUÔN dùng lunar year khi tính Can Chi (không solar year) — bug critical
- ⚠️ TypedDict với keys tiếng Việt OK nhưng tránh — dùng snake_case English
- ⚠️ Comments tiếng Việt cho phần liên quan văn hoá (mệnh, tam hợp...)
