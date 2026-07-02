# PLAN — Sprint hiện tại
# File: docs/PLAN.md

> Sprint: 1/8 — Foundation (Tuần 1-2, Tháng 1 — theo TalentChart_Strategy_Phase12)
> Owner: Trung (kiến trúc/review) — Mid Dev (triển khai chính) — Intern 1&2 (hỗ trợ)

## Mục tiêu sprint

Dựng nền tảng multi-tenant an toàn: xác thực, phân quyền, cô lập dữ liệu theo tổ chức (organization). Đây là sprint quan trọng nhất — mọi module sau đều build trên nền này, và lỗi ở đây (data leak tenant) là rủi ro lớn nhất của dự án.

## Deliverables

- [x] `backend/app/models/base.py` — `TenantScopedBase` (organization_id NOT NULL, id UUID, created_at/updated_at, status) — DRI: Mid Dev
- [x] `backend/app/models/organization.py`, `backend/app/models/user.py` — DRI: Mid Dev
- [x] `backend/app/middleware/tenant.py` — resolve org theo thứ tự JWT → subdomain → header dev — DRI: Mid Dev
- [x] `backend/app/core/security.py` — JWT (access 15p/refresh 7 ngày) + bcrypt cost 12 — DRI: Mid Dev
- [x] `backend/app/routers/auth.py` — `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` — DRI: Mid Dev
- [x] PostgreSQL RLS policy cho `users` — đã viết trong migration `0001` (ENABLE + FORCE + policy theo `app.current_org_id`) — **chờ Trung review trước khi chạy trên staging**
- [x] `backend/tests/test_tenant_isolation.py` — 26 test pass (isolation + auth), coverage 90%
- [ ] Docker Compose local chạy được (`db`, `redis`, `backend`) — `docker-compose.dev.yml` đã viết, **chưa verify** (máy scaffold không có Docker) — DRI: Intern 1

## User stories

### Story 1: Đăng nhập theo tổ chức
**As a** quản trị viên của một trường/tổ chức
**I want** đăng nhập bằng email + mật khẩu trong phạm vi tổ chức của mình
**So that** không thể đăng nhập nhầm hoặc thấy dữ liệu tổ chức khác

**Acceptance criteria:**
- [ ] Email/username unique trong phạm vi `organization_id`, không unique toàn hệ thống
- [ ] Sai mật khẩu 5 lần/phút/IP bị rate-limit (429)
- [ ] Access token JWT chứa `user_id, organization_id, org_role, system_role`

**Technical notes:**
- API endpoints: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `GET /api/v1/auth/me`
- Models: `Organization`, `User` (kế thừa `TenantScopedBase` trừ `Organization` là bảng root không tenant-scoped)
- Migration: tạo bảng `organizations`, `users` + enable RLS

### Story 2: Cô lập dữ liệu giữa các tổ chức (tenant isolation)
**As a** chủ hệ thống TalentChart
**I want** đảm bảo tổ chức A không bao giờ truy cập được dữ liệu tổ chức B
**So that** tránh sự cố "1 bug leak tenant = giết startup"

**Acceptance criteria:**
- [ ] Mọi query ORM tự động filter `organization_id` qua SQLAlchemy event listener
- [ ] Truy cập resource của tổ chức khác trả về 404 (không phải 403)
- [ ] RLS bật cho bảng `users` (`ALTER TABLE users ENABLE ROW LEVEL SECURITY`)
- [ ] Test `test_tenant_isolation.py` tạo 2 org + 2 user, xác nhận user org A không list/get được user org B

**Technical notes:**
- Xem `~/hpu-dev/skills/multi-tenant-saas/SKILL.md` để lấy pattern middleware + event listener + RLS đầy đủ
- `.claude/rules/tenant-isolation.md` là rule bắt buộc, `/security-review` sẽ tự động kiểm tra 7 quy tắc này

## Tasks technical

### Backend
- [ ] Setup `pyproject.toml` (uv), cấu hình `ruff`/`mypy`/`pytest` — Mid Dev — ngày 1-2
- [ ] `config.py` — Settings fail-fast (JWT_SECRET không có default) — Mid Dev — ngày 2
- [ ] `models/base.py` (TenantScopedBase) + `database.py` (async engine + event listener filter) — Mid Dev — ngày 3-4
- [ ] `models/organization.py`, `models/user.py` + Alembic migration đầu tiên — Mid Dev — ngày 4-5
- [ ] `middleware/tenant.py`, `middleware/auth.py` — Mid Dev — ngày 6-7
- [ ] `core/security.py`, `routers/auth.py` — Mid Dev — ngày 7-8
- [ ] RLS policy SQL cho `users` — Trung — ngày 8
- [ ] `tests/test_tenant_isolation.py` — Intern 2 — ngày 9-10

### Frontend
- [ ] Scaffold Next.js 15 App Router, cấu hình Tailwind + shadcn/ui — Intern 1 — ngày 1-3
- [ ] Trang `(auth)/login` — Intern 1 — ngày 4-6
- [ ] `lib/api-client.ts` (gắn JWT vào header) — Intern 1 — ngày 7-8

### DevOps / Testing
- [ ] `docker-compose.yml` chạy local (db, redis, backend) — Intern 1 — ngày 1-2
- [ ] GitHub Actions CI cơ bản (test backend) — Trung — ngày 9-10
- [ ] `/security-review` chạy trên toàn bộ module auth/tenant trước khi merge — Trung — ngày 10

## Out of scope (không làm trong sprint này)

- Module ATS (candidates/campaigns) — Sprint 2-3
- EPA Engine — Sprint 5
- Job Board / Career Page — Sprint 4
- Frontend dashboard hoàn chỉnh — Sprint 7

## Dependencies / Risks

- Phụ thuộc: cần có server/máy dev đã cài Docker + đã chạy `~/hpu-dev/setup.sh` và tạo network `caddy-proxy`
- Risk: Mid dev mới join, chưa quen multi-tenant pattern — mitigation: Trung pair review kỹ ADR-003 và skill `multi-tenant-saas` trước khi code
- Risk: RLS cấu hình sai khiến mọi query bị chặn — mitigation: viết test isolation sớm ngày 9, không để cuối sprint

## Definition of Done

- [ ] Code merged vào main
- [ ] Tests viết và pass (bao gồm `test_tenant_isolation.py`)
- [ ] `/security-review` clean (đặc biệt mục Multi-tenant safety)
- [ ] `/review` clean (7 tiêu chí HPU)
- [ ] Deployed lên staging
- [ ] User (Trung) accept testing pass — login + xác nhận cô lập tenant qua Postman/curl
- [ ] Documentation updated — `docs/DECISIONS.md` (nếu có quyết định mới phát sinh), `docs/API.md`

## Daily standup notes

### Day 1
- Done: —
- Today: Setup project skeleton (backend + frontend + docker)
- Blocker: —

### 2026-07-02 (Claude Code — backend foundation)
- Done: toàn bộ backend Sprint 1 — config fail-fast, TenantScopedBase, Organization/User,
  database.py (event listener auto-filter + flush guard + RLS GUC), middleware auth/tenant,
  JWT + bcrypt 12, routers auth (login/refresh/me) + users (list/get), migration Alembic 0001
  kèm RLS policy, 26 test pass (isolation + auth), coverage 90%, ruff sạch.
  Sửa backend/Dockerfile (template cũ sai), thêm docker-compose.dev.yml + scripts/create_tenant.py.
- Next: Trung review RLS policy (migration 0001); Intern 1 verify docker-compose.dev.yml
  trên máy có Docker + chạy `alembic upgrade head`; scaffold frontend Next.js 15 (login page,
  api-client); GitHub Actions CI.
- Blocker: máy scaffold không có Docker/uv → chưa verify compose + migration trên PostgreSQL thật
  (test chạy trên SQLite in-memory, RLS chỉ verify được trên PG).
