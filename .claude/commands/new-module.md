# /new-module — Tạo CRUD module mới

Áp dụng cho: Cả Internal Tool và SaaS

## Khi nào dùng

User chạy `/new-module {entity}` để scaffold một module CRUD mới.

Ví dụ:
- `/new-module employees` (Internal: hpu-hrm)
- `/new-module candidates` (SaaS: TalentChart)

## Việc cần làm

### Step 1 — Detect project type

Kiểm tra:
- Có file `src/models/base.py` với `TenantScopedBase` → SaaS multi-tenant
- Có file `src/models.py` đơn giản → Internal Tool

Áp dụng pattern tương ứng theo skill `fastapi-crud`.

### Step 2 — Hỏi user thông tin

- Tên entity (singular): `employee`, `candidate`, `job_post`...
- Fields chính (ngoài id/created_at/updated_at/status):
  - Tên field, type, nullable, unique, index
- Liên kết với entity nào? (department, organization...)
- Permissions: ai được tạo / sửa / xóa?

### Step 3 — Tạo files (theo project type)

**Internal Tool:**
```
src/models.py                          ← Thêm class Employee
src/schemas.py                         ← Thêm EmployeeCreate, EmployeeResponse
src/routes/{entity}_routes.py          ← 6 endpoints CRUD
src/templates/{entity}/list.html       ← UI list
src/templates/{entity}/form.html       ← UI form
tests/test_{entity}.py                 ← Tests
```

**SaaS:**
```
src/models/{entity}.py                 ← TenantScopedBase
src/schemas/{entity}.py                ← Pydantic schemas (KHÔNG có org_id)
src/routes/{entity}_routes.py          ← 6 endpoints async + tenant verify
src/services/{entity}_service.py       ← Business logic (optional)
alembic/versions/xxx_add_{entity}.py   ← Migration
tests/test_{entity}.py                 ← Tests + tenant isolation tests
```

### Step 4 — Register

```python
# src/main.py
from src.routes import {entity}_routes
app.include_router({entity}_routes.router)
```

### Step 5 — Migration (SaaS)

```bash
docker compose exec backend uv run alembic revision --autogenerate -m "add_{entity}_table"
docker compose exec backend uv run alembic upgrade head
```

### Step 6 — Run tests

```bash
docker compose exec backend uv run pytest tests/test_{entity}.py -v
```

## Output cho user

```
✅ Module {entity} đã được tạo

📁 Files mới:
- src/models/{entity}.py (hoặc src/models.py thêm class)
- src/schemas/{entity}.py
- src/routes/{entity}_routes.py
- tests/test_{entity}.py
- alembic/versions/xxx... (SaaS only)

🔗 API endpoints:
- GET    /api/v1/{entities}
- GET    /api/v1/{entities}/{id}
- POST   /api/v1/{entities}
- PUT    /api/v1/{entities}/{id}
- DELETE /api/v1/{entities}/{id}
- GET    /api/v1/{entities}/export

📝 Bước tiếp theo:
1. Review code generated
2. Adjust fields/validation theo nghiệp vụ
3. Add UI templates (Internal) hoặc Next.js page (SaaS)
4. Add to sidebar nav
```

## Checklist BẮT BUỘC

- [ ] Pydantic Create schema KHÔNG có id, organization_id, created_at
- [ ] Response schema KHÔNG include sensitive fields
- [ ] LIST endpoint có pagination
- [ ] DELETE là soft delete (status="inactive")
- [ ] Money fields dùng Integer
- [ ] Response dùng helper `success()/paginated()`
- [ ] Error message tiếng Việt
- [ ] Test có tenant isolation case (SaaS)
- [ ] Migration có upgrade() và downgrade() (SaaS)
