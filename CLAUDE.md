# talentchart — Nền tảng SaaS tuyển dụng và đánh giá nhân sự tích hợp Eastern Personality Assessment (EPA)
# CLAUDE.md — Project instructions cho Claude Code

> **Loại app:** SaaS Multi-tenant (Next.js 15 + PostgreSQL + JWT + Multi-tenant)

## Project Overview
TalentChart — nền tảng SaaS B2B tuyển dụng & đánh giá nhân sự đầu tiên tại Việt Nam tích hợp Eastern Personality Assessment (EPA — đánh giá tính cách theo khung Á Đông: Can Chi/Mệnh/Tam hợp) với ATS hiện đại và AI. Hợp nhất 3 hệ thống nguồn: SmartHire (ATS), Phần mềm Tuyển dụng, Fortune HR (tử vi). Khách hàng số 0: HPU (150 CB-GV, 2.000 SV). Đối tượng: trường ĐH/CĐ (lõi) và HR agency. Định vị "Eastern Personality Assessment Platform for Modern HR" — không tự nhận là phần mềm tử vi.

## Tech Stack

### Backend
- Python 3.12, FastAPI 0.115+, SQLAlchemy 2.0 async
- PostgreSQL 16 (multi-tenant với Row Level Security)
- Redis 7 (cache, rate limit, Celery queue)
- Celery (background jobs: parse CV, sinh PDF)
- Pydantic v2, Alembic migrations
- JWT auth (15min access + 7day refresh)
- MinIO (S3-compatible) cho file storage

### Frontend
- Next.js 15 App Router + TypeScript 5.6 strict
- Tailwind CSS 3.4 + shadcn/ui (copy components)
- TanStack Query (server state) + Zustand (client state)
- React Hook Form + Zod validation
- Lucide icons, date-fns vi locale

### DevOps
- Docker + Docker Compose
- Caddy + caddy-docker-proxy (label-based, auto SSL)
- GitHub Actions CI
- Self-host trên server HPU

### Deploy
- Backend: `app.talentchart.hpu.edu.vn:8003`
- Frontend admin: `app.talentchart.hpu.edu.vn`
- Public per-tenant: `{org-slug}.talentchart.hpu.edu.vn`

## Commands

```bash
# Dev
docker compose -f docker-compose.dev.yml up -d
docker compose exec backend uvicorn app.main:app --reload
cd frontend && pnpm dev

# Migration
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "..."

# Tests
docker compose exec backend pytest -v
docker compose exec backend pytest --cov=app
cd frontend && pnpm test

# Lint + typecheck
docker compose exec backend ruff check . --fix
docker compose exec backend mypy app/
cd frontend && pnpm lint && pnpm typecheck

# Production
docker compose --env-file .env.production up -d --build
```

## Architecture

```
backend/
├── app/
│   ├── main.py             — FastAPI app, middleware setup
│   ├── config.py           — Settings (fail-fast)
│   ├── database.py         — Async session + tenant filter event listener
│   ├── celery_app.py       — Celery config
│   ├── exceptions.py       — Custom exceptions
│   ├── middleware/
│   │   ├── tenant.py       — ★ Multi-tenant middleware (CRITICAL)
│   │   ├── auth.py         — JWT validation
│   │   ├── rate_limit.py
│   │   └── audit.py
│   ├── core/
│   │   ├── responses.py    — success/error/paginated helpers
│   │   ├── security.py     — JWT, password hashing
│   │   ├── permissions.py  — RBAC (OrgRole)
│   │   └── tenant_context.py
│   ├── models/
│   │   ├── base.py         — ★ TenantScopedBase
│   │   ├── organization.py
│   │   ├── user.py
│   │   ├── candidate.py
│   │   └── ...
│   ├── schemas/            — Pydantic (KHÔNG có org_id)
│   ├── routers/
│   ├── services/
│   │   └── epa/            — EPA Engine (TalentChart only)
│   │       ├── lunar.py
│   │       ├── canchi.py
│   │       └── archetype.py
│   └── tasks/              — Celery tasks
├── alembic/
└── tests/
    └── test_tenant_isolation.py  — ★ CRITICAL tests

frontend/
├── src/
│   ├── app/
│   │   ├── (public)/        — Public pages (career, landing)
│   │   ├── (auth)/          — Login pages
│   │   └── (admin)/         — Protected admin app
│   ├── components/
│   │   ├── ui/              — shadcn components
│   │   └── features/
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── utils.ts
│   └── hooks/
└── middleware.ts            — Subdomain routing

docs/
├── PLAN.md
├── DECISIONS.md             — ADRs
├── API.md
└── architecture.md
```

## Multi-Tenant Rules (CRITICAL — đọc kỹ)

⚠️ **Một bug data leak tenant = giết startup.** Áp dụng nghiêm ngặt:

1. Mọi bảng dữ liệu khách hàng inherit `TenantScopedBase` (có `organization_id NOT NULL`)
2. Mọi query filter `organization_id` (auto qua middleware + event listener)
3. Cross-tenant access trả 404, KHÔNG 403
4. Pydantic Create schema KHÔNG có `organization_id`
5. PostgreSQL RLS bật cho mọi bảng tenant-scoped
6. Test isolation BẮT BUỘC cho mọi module CRUD

Đọc đầy đủ: `~/hpu-dev/skills/multi-tenant-saas/SKILL.md`

## Skills tự động load
- `fastapi-crud` — tạo module CRUD
- `multi-tenant-saas` — tenant safety patterns
- `nextjs-admin` — Next.js 15 frontend
- `docker-deploy` — deploy với caddy-docker-proxy
- `epa-engine` — bát tự, 12 archetype (TalentChart)

## Slash commands available
- `/new-module {entity}` — tạo CRUD module multi-tenant
- `/new-tenant {slug}` — tạo organization mới
- `/epa-port {module}` — port logic JS → Python (TalentChart)
- `/security-review` — security audit (đặc biệt tenant safety)
- `/review` — code review 7 tiêu chí
- `/deploy` — build + deploy

## Critical Business Rules
- Pipeline ứng viên gồm các trạng thái `NEW → SCREENING → TEST_SENT → TEST_DONE → INTERVIEW → DECISION → HIRED/REJECTED`, đi TIẾN tuần tự từng bước (không nhảy cóc, không đi lùi). Riêng `REJECTED` (từ chối) được phép chuyển tới từ BẤT KỲ bước chưa kết thúc — xem ADR-007. Không rời khỏi trạng thái kết thúc (HIRED/REJECTED). `HIRED` chỉ vào được từ `DECISION`.
- `candidates` hợp nhất applicant/employee/student/alumni qua field `candidate_type` — không tách bảng riêng.
- EPA Engine phải **port nguyên xi** thuật toán từ Fortune HR (`legacy/fortune-hr/`), tuyệt đối không "cải tiến" công thức Can Chi/Nạp Âm/Mệnh khi port — nếu test lệch kết quả gốc thì đó là bug port, phải sửa code port chứ không sửa thuật toán.
- Tính Can Chi bắt buộc dùng **năm âm lịch (lunar year)**, không dùng năm dương lịch — đây là bug đã từng xảy ra ở hệ cũ, sinh trước Tết phải tính theo năm âm lịch trước đó.
- 12 Personality Archetype = fusion DISC (16 profile) + Mệnh (5 hành) + Tam hợp (4 nhóm) + narrative do Claude API sinh. Riêng phần mô tả gốc của 12 archetype là do Trung viết tay (core IP) — AI chỉ polish câu chữ, không tự sáng tác nội dung archetype mới.
- EPA có 2 lớp hiển thị: Behavioural Layer (mặc định, dùng cho B2B — chỉ DISC + archetype) và Eastern Layer (toggle riêng — hiện thêm mệnh/nạp âm/tam hợp). Mặc định tắt Eastern Layer trừ khi tenant bật.
- EPA score/kết quả trắc nghiệm không được là yếu tố quyết định DUY NHẤT trong quyết định tuyển dụng — chỉ là 1 tín hiệu tham khảo.
- Dữ liệu ngày/giờ/nơi sinh dùng để tính EPA là dữ liệu nhạy cảm — thu thập theo cơ chế opt-in, tuân thủ Nghị định 13/2023/NĐ-CP (quyền xoá trong 30 ngày, mã hoá at-rest).
- Username/email của `users` unique **trong phạm vi organization**, không unique toàn hệ thống.
- Money luôn Integer VNĐ (xem `.claude/rules/money-integer.md`).

## Gotchas
- ⚠️ KHÔNG dùng raw SQL — chỉ ORM
- ⚠️ Mọi query mới phải verify có tenant filter
- ⚠️ Async/await cho mọi I/O
- ⚠️ JWT_SECRET fail-fast, KHÔNG default
- ⚠️ Migration test trên staging trước
- ⚠️ Background task nặng dùng Celery, KHÔNG BackgroundTasks
- ⚠️ Subdomain routing đã setup ở middleware.ts (Next.js)

## Shared Resources
- Design system: ~/hpu-dev/_shared/design-system/
- API conventions: ~/hpu-dev/_shared/api-conventions.md (xem section Multi-tenant)
- DB conventions: ~/hpu-dev/_shared/db-conventions.md (xem TenantScopedBase)
- Auto-rules: .claude/rules/ (đặc biệt tenant-isolation.md)

## Workflow
1. **Claude.ai**: brainstorm + design + viết spec
2. Copy spec vào `docs/PLAN.md`
3. **Claude Code**: `claude` → load CLAUDE.md + skills → triển khai
4. Mỗi feature có ADR trong `docs/DECISIONS.md`
5. Test isolation BẮT BUỘC trước merge
6. `/security-review` trước deploy production
7. `/deploy` → verify → notify
