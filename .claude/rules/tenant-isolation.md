# Rule: Tenant Isolation (SaaS only)

⚠️ **CRITICAL — vi phạm rule này có thể giết startup ngay lập tức.**

## Áp dụng cho

Mọi project SaaS multi-tenant (TalentChart...).
Project là SaaS nếu có file `src/models/base.py` với class `TenantScopedBase`.

## Quy tắc

### 1. Mọi bảng tenant-scoped PHẢI có `organization_id NOT NULL`

```python
# ✅ ĐÚNG — inherit TenantScopedBase
class Candidate(TenantScopedBase):
    __tablename__ = "candidates"
    full_name = Column(String(100), nullable=False)
    # organization_id, id, status, created_at, updated_at đã có từ base

# ❌ SAI — inherit Base trực tiếp
class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(UUID, primary_key=True)
    # Thiếu organization_id!
```

### 2. Mọi query PHẢI có org filter

```python
# ✅ ĐÚNG — filter explicit
result = await db.execute(
    select(Candidate)
    .where(Candidate.id == id)
    .where(Candidate.organization_id == current_org_id)
)

# ✅ ĐÚNG — auto qua SQLAlchemy event listener
result = await db.execute(select(Candidate))  # Listener tự inject filter

# ❌ SAI — IDOR vulnerability
result = await db.get(Candidate, id)
```

### 3. Cross-tenant access trả 404, KHÔNG 403

```python
# ✅ ĐÚNG
if not candidate or candidate.organization_id != current_org_id:
    raise ResourceNotFound("Candidate")  # → 404

# ❌ SAI — leak existence
if candidate.organization_id != current_org_id:
    raise PermissionError("Access denied")  # → 403 leak rằng resource tồn tại
```

### 4. Pydantic Schema Create KHÔNG có `organization_id`

```python
# ✅ ĐÚNG
class CandidateCreate(BaseModel):
    full_name: str
    email: EmailStr
    # ❌ KHÔNG có: organization_id, id, created_at

# ❌ SAI — client có thể inject org_id của tenant khác
class CandidateCreate(BaseModel):
    full_name: str
    organization_id: UUID  # KHÔNG được phép!
```

### 5. organization_id set từ context, KHÔNG từ client

```python
# ✅ ĐÚNG
@router.post("")
async def create(data: CandidateCreate, user = Depends(get_current_user)):
    item = Candidate(
        **data.model_dump(),
        organization_id=user.organization_id  # Từ JWT context
    )
```

### 6. Response schema KHÔNG include `organization_id`

```python
# ✅ ĐÚNG
class CandidateResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    # ❌ KHÔNG include organization_id để tránh leak

# ❌ SAI
class CandidateResponse(BaseModel):
    id: UUID
    organization_id: UUID  # Leak!
    full_name: str
```

### 7. Test isolation BẮT BUỘC

```python
# ✅ Mỗi module CRUD phải có test này
async def test_user_cannot_access_other_org_resource(
    async_client, hr_manager_org_a, candidate_org_b
):
    headers = auth_headers(hr_manager_org_a)
    response = await async_client.get(
        f"/api/v1/candidates/{candidate_org_b.id}", headers=headers
    )
    assert response.status_code == 404  # KHÔNG 403
```

## Vi phạm = block merge

Code review tự động chạy `/security-review` sẽ flag những vi phạm trên là **CRITICAL**. Không được merge vào main.
