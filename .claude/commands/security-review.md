# /security-review — Security audit toàn module hoặc PR

Áp dụng cho: Mọi project (Internal Tool và SaaS), nhưng đặc biệt cho SaaS multi-tenant.

## Khi nào dùng

User chạy `/security-review` để audit security toàn diện một module hoặc trước khi deploy production.

Có thể chạy với:
- `/security-review` → audit toàn project
- `/security-review candidates` → audit module cụ thể
- `/security-review --pr` → audit code thay đổi trong PR hiện tại

## Việc cần làm

Đóng vai SECURITY AUDITOR chuyên penetration test. Kiểm tra theo 12 categories sau:

### 1. Multi-tenant safety (CRITICAL — chỉ SaaS)

Tìm các issues:
- Query thiếu `organization_id` filter
- Endpoint nhận resource id không verify tenant ownership (IDOR)
- Trả về 403 thay vì 404 cho cross-tenant access (leak existence)
- Pydantic schema cho phép client set `organization_id`
- Filter ở Python sau khi đã query (slow + leak)
- Raw SQL không có org context

```bash
# Auto-detect pattern
grep -rn "session.get\|session.query.*get\|select.*where(.*\.id ==" src/ \
  | grep -v "organization_id"
```

### 2. SQL Injection

Tìm:
- Raw SQL với string concatenation
- f-string trong query
- `text()` với user input không escape

```bash
grep -rn "execute(f\|execute(.*+\|execute(.*%" src/
grep -rn "text(f\|text(.*+" src/
```

### 3. XSS (Cross-Site Scripting)

Tìm:
- Jinja2 template không dùng `|e` filter cho user input
- React/Next.js dangerouslySetInnerHTML
- HTML rendering chưa escape

### 4. Authentication

Kiểm tra:
- JWT_SECRET có default value không (CẤM)
- bcrypt cost factor >= 10
- Token TTL hợp lý (access <30min, refresh <7 days)
- Force change password lần đầu login
- Rate limit login (5 fail / 15 phút lock)

### 5. Authorization

Kiểm tra:
- Mọi endpoint protected có `Depends(get_current_user)` hoặc `require_auth`
- RBAC decorator (`@require_org_role`) có cho mỗi endpoint cần permission
- BGH/Viewer chỉ READ, không WRITE
- Public endpoint có rate limit

### 6. Mass Assignment

Tìm:
- Pydantic Create schema có field nhạy cảm: `organization_id`, `id`, `role`, `is_admin`, `created_at`
- `**data.model_dump()` mà không filter

### 7. Information Disclosure

Tìm:
- Error message leak stack trace ra production
- Log password, token, JWT, full PII
- Response trả về model object trực tiếp (không qua Response schema)
- Exception message expose internal paths/queries

### 8. CSRF

Kiểm tra:
- Internal Tool (session cookie): có CSRF token cho POST không
- SaaS (JWT): SameSite cookie config, CORS đúng

### 9. Cryptographic

Kiểm tra:
- KHÔNG dùng MD5, SHA1 cho password (chỉ bcrypt/argon2)
- Secret key min 32 chars random
- HTTPS-only cookie (secure=True)

### 10. Rate Limiting

Kiểm tra có rate limit cho:
- Login: 5 req/phút/IP
- Password reset: 3 req/phút/IP
- Public API endpoints
- Test submission (token-based)
- Export endpoints: 5 req/phút/user

### 11. Dependency vulnerabilities

```bash
# Python
docker compose exec backend uv run pip audit
# Or
docker compose exec backend uv run safety check

# JavaScript
cd frontend && pnpm audit
```

### 12. Anti-patterns AI hay sinh ra

Tìm:
- TODO, FIXME, your-key-here, placeholder
- time.sleep() trong async code
- catch generic Exception và swallow
- N+1 query
- Race condition trong concurrent update

```bash
grep -rn "TODO\|FIXME\|your-.*-here\|XXX" src/
grep -rn "time.sleep" src/
grep -rn "except Exception:\s*pass" src/
```

## Format Report

```markdown
# Security Review Report — {date}

## Tổng quan
- Module: {module hoặc "toàn project"}
- Critical issues: {N}
- High issues: {N}
- Medium issues: {N}
- Low issues: {N}

## Issues chi tiết

### [CRITICAL] #1 — Tenant isolation leak ở /api/v1/candidates/{id}

**Vị trí:** src/routes/candidates_routes.py:42

**Vấn đề:**
Endpoint `get_candidate(id)` lookup trực tiếp by id không verify tenant.

```python
# Code có vấn đề
@router.get("/{id}")
async def get_candidate(id: UUID, db = Depends(get_db)):
    return await db.get(Candidate, id)  # ❌ Không filter organization_id
```

**Cách exploit:**
User của org A có thể request `GET /api/v1/candidates/{id-of-org-B-candidate}`
và lấy được data của tenant khác.

**Severity rationale:** CRITICAL — leak data khách hàng giữa các tenant.

**Đề xuất fix:**
```python
@router.get("/{id}")
async def get_candidate(id: UUID, db = Depends(get_db), user = Depends(get_current_user)):
    org_id = get_current_org_id_required()
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == id)
        .where(Candidate.organization_id == org_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise ResourceNotFound("Candidate")  # 404, KHÔNG 403
    return success(CandidateResponse.model_validate(item))
```

**Test case bổ sung:**
```python
async def test_cannot_access_other_org_candidate(...):
    # Verify trả 404 khi truy cập cross-tenant
```

### [HIGH] #2 — ...

## Tóm tắt action items

1. [CRITICAL] Fix tenant isolation ở candidates router
2. [CRITICAL] ...
3. [HIGH] Add rate limit cho login endpoint
...

## OK — không tìm thấy vấn đề ở các phần sau
- ✅ Password hashing (bcrypt cost 12)
- ✅ JWT secret từ env (no default)
- ...
```

## Gotchas

- ⚠️ Đừng bịa ra issue để có gì để báo cáo. Nếu code OK, nói rõ "không tìm thấy issue đáng kể"
- ⚠️ CRITICAL = có thể exploit ngay, ảnh hưởng customer hiện tại
- ⚠️ HIGH = có thể exploit nhưng cần điều kiện, hoặc ảnh hưởng tương lai
- ⚠️ MEDIUM = best practice, nên fix nhưng chưa cấp bách
- ⚠️ LOW = code smell, refactor opportunity
- ⚠️ Mỗi issue PHẢI có: vị trí, cách exploit, đề xuất fix code, test case
- ⚠️ Đặc biệt focus multi-tenant cho SaaS — đây là attack vector nguy hiểm nhất
