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
- [x] Setup `pyproject.toml` (uv), cấu hình `ruff`/`mypy`/`pytest` — Mid Dev — ngày 1-2
- [x] `config.py` — Settings fail-fast (JWT_SECRET không có default) — Mid Dev — ngày 2
- [x] `models/base.py` (TenantScopedBase) + `database.py` (async engine + event listener filter) — Mid Dev — ngày 3-4
- [x] `models/organization.py`, `models/user.py` + Alembic migration đầu tiên — Mid Dev — ngày 4-5
- [x] `middleware/tenant.py`, `middleware/auth.py` — Mid Dev — ngày 6-7
- [x] `core/security.py`, `routers/auth.py` — Mid Dev — ngày 7-8
- [x] RLS policy SQL cho `users` — Trung — ngày 8
- [x] `tests/test_tenant_isolation.py` — Intern 2 — ngày 9-10

### Frontend
- [x] Scaffold Next.js 15 App Router, cấu hình Tailwind + shadcn/ui — Intern 1 — ngày 1-3
- [x] Trang `(auth)/login` — Intern 1 — ngày 4-6
- [x] `lib/api-client.ts` (gắn JWT vào header) — Intern 1 — ngày 7-8

### DevOps / Testing
- [ ] `docker-compose.yml` chạy local (db, redis, backend) — Intern 1 — ngày 1-2
- [x] GitHub Actions CI cơ bản (test backend) — Trung — ngày 9-10
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

### 2026-07-03 (Claude Code — Sprint 2-4 backend + frontend Sprint 1)
- Done:
  - **Sprint 2-3 (ATS Core)**: module `campaigns` + `candidates` — pipeline 7 trạng thái
    tuần tự (state machine trong `services/candidate_service.py`, vi phạm → 422),
    candidate_type hợp nhất, EPA opt-in consent theo NĐ 13/2023 (rút consent = xóa data,
    endpoint DELETE /candidates/{id}/epa-data), guard IDOR campaign cross-tenant,
    stats endpoint. Migration 0002 + RLS cho 3 bảng.
  - **Sprint 4 (Job Board)**: module `job_posts` (slug unique/org, tự slugify tiếng Việt,
    publish/unpublish) + public career API theo subdomain (GET /public/jobs,
    POST /public/jobs/{slug}/apply → tạo candidate NEW, rate-limit 10/min, chặn nộp trùng).
  - **Sprint 1 frontend**: Next.js 15 scaffold, login page (RHF+zod), api-client
    (JWT + auto refresh), zustand store, middleware.ts subdomain→/career/{slug},
    career page SSR, dashboard tối giản. Đã verify end-to-end trên browser thật:
    login → dashboard → /auth/me + /candidates/stats. Thêm CORSMiddleware backend.
  - CI GitHub Actions (backend pytest+ruff+coverage≥70%, frontend typecheck+build).
  - Backend: 65 test pass, ruff sạch. Frontend: typecheck + build pass.
- Next: Trung review RLS + acceptance test; Sprint 5 EPA Engine.
- **Blocker Sprint 5-6**: `legacy/fortune-hr/` và `legacy/smarthire-html/` ĐANG RỖNG —
  theo CLAUDE.md phải port nguyên xi từ code nguồn, KHÔNG được tự sáng tác thuật toán
  Can Chi/DISC. Cần Trung copy code nguồn Fortune HR (server.js chứa LunarData) và
  SmartHire vào legacy/ trước khi chạy /epa-port. Nội dung 12 archetype cũng chờ
  bản viết tay của Trung (core IP).
- Lưu ý: pipeline hiện enforce đúng theo Critical Business Rules (chỉ tuần tự, DECISION
  → HIRED/REJECTED) — nghĩa là muốn loại ứng viên sớm phải đi qua đủ các bước.
  Nếu nghiệp vụ thực tế cần "REJECTED từ bất kỳ bước nào", cần Trung quyết và
  sửa rule trong CLAUDE.md + ADR trước khi đổi code.

### 2026-07-04 (Claude Code — DISC port + Google OAuth + rà soát tổng thể)
- Done:
  - **DISC port từ SmartHire** (tìm thấy nguồn tại D:/PROJECT/hpu-smart-hire — Python):
    copy nguồn vào `legacy/smarthire-html/`, port NGUYÊN XI 40 câu DISC + 30 câu
    personality (9 nhóm) + toàn bộ thuật toán chấm điểm/phân tích/gợi ý phỏng vấn.
    `tests/test_disc_parity.py` load trực tiếp file legacy và so khớp 29 bộ trả lời
    (25 random seeded + 4 edge case) — khớp 100%. Cải tiến duy nhất (không đụng thuật
    toán): câu hỏi public KHÔNG kèm mapping D/I/S/C (hệ cũ nhúng đáp án vào HTML).
  - **Flow test**: TestSession (migration 0003 + RLS), POST /test-links (pipeline
    SCREENING→TEST_SENT, gửi lại = vô hiệu link cũ), public GET/submit theo token
    (→TEST_DONE), kết quả HR đầy đủ / ứng viên chỉ Behavioural Layer.
  - **Google OAuth (ADR-004)**: staff login theo Workspace domain per-tenant
    (HPU = hpu.edu.vn, auto-provision member), ứng viên Google bất kỳ với JWT
    type=candidate riêng + candidate portal (/me, /me/test). Nút Google trên login
    page (GIS, tự ẩn khi chưa cấu hình NEXT_PUBLIC_GOOGLE_CLIENT_ID).
  - **Frontend**: trang làm bài /test/{token} (2 phần, progress bar, chặn most=least,
    màn hình kết quả DISC).
  - **Rà soát**: backend 124 test pass + ruff sạch; frontend typecheck + build pass;
    e2e trên browser thật: tạo candidate → SCREENING → gửi link → làm đủ 70 câu trên UI
    → nộp → kết quả D/60-0-20-20 → pipeline TEST_DONE → HR xem kết quả đầy đủ.
- Next: điền GOOGLE_CLIENT_ID thật (tạo trên Google Cloud Console, authorized origins
  = app.talentchart.hpu.edu.vn + *.talentchart... + localhost:3000) rồi test Google
  login thật; Trung review RLS 3 migration; Sprint 5 EPA vẫn chờ code Fortune HR.
- Blocker: `legacy/fortune-hr/` vẫn RỖNG (Can Chi/EPA — Sprint 5); Google login chưa
  test với token thật (chưa có GOOGLE_CLIENT_ID — mock trong test).

### 2026-07-05 (Claude Code — Sprint 5 EPA Engine + import nhân sự)
- Done:
  - **EPA port từ Fortune HR v6.2** (Trung đã copy nguồn vào D:/PROJECT/hpu-smart-hire/
    fortune-hr-v6.2, tôi copy tiếp vào legacy/fortune-hr/): port NGUYÊN XI LunarData
    1900-2099, getLunarDate, Can Chi/Nạp Âm/Mệnh theo NĂM ÂM LỊCH, Tam hợp/Xung,
    compatibility (50 +25 −30), team-suggest. Thành `app/services/epa/{lunar,canchi,
    tamhop,compatibility,team_suggest}.py`.
  - **Parity 300 case**: fixture sinh bằng cách CHẠY code JS gốc qua Node (TZ=UTC —
    phát hiện code gốc phụ thuộc timezone do tzdata lịch sử VN; production Docker
    chạy UTC nên chuẩn hành vi = số học ngày thuần). Case bắt buộc 1/1/1938 → Đinh Sửu ✓.
    Quirk giữ nguyên khi port: cùng địa chi → điểm 45 (vừa +25 tam hợp vừa −30 xung).
  - **EPA API**: /epa/today, /epa/candidates/{id}/zodiac, /epa/compatibility,
    /epa/team-suggest — gate 2 lớp: org.settings.eastern_layer_enabled (mặc định TẮT)
    + epa_consent/birth_date từng người; mọi response kèm disclaimer.
  - **Import nhân sự từ "Luong T8 gửi Trung.xlsx"**: scripts/import_employees.py —
    107 nhân sự (file có 2 phân đoạn TT đánh lại + 2 hàng rác "Copy" đã lọc),
    candidate_type=employee, pipeline HIRED, employee_code NV0001-0107, KHÔNG import
    lương, ngày sinh chỉ khi --with-epa-consent. Migration 0004 thêm employee_code +
    department. Email placeholder @import.hpu.edu.vn chờ cập nhật email thật.
  - **E2E trên dữ liệu thật**: Trần Hữu Nghị (1/1/1938) → Đinh Sửu/Mệnh Thủy qua API;
    team-suggest HCTH 21 người. Backend 447 test pass, ruff sạch, typecheck pass.
- Next: Trung cập nhật email thật cho 107 nhân sự (match Google login); Sprint 6
  (12 Archetype fusion — CẦN nội dung viết tay của Trung, AI chỉ polish); Sprint 7
  frontend dashboard + màn EPA.
- Blocker Sprint 6: nội dung gốc 12 Personality Archetype (core IP — Trung viết tay).

### 2026-07-05 chiều (Claude Code — Sprint 6: 12 Archetype + đối chiếu danh bạ)
- Done:
  - **12 Personality Archetype (ADR-005)**: Trung cung cấp docs/DISC-Tieng-Viet.pdf
    (báo cáo DISCstyles 40 trang) làm nguồn nội dung. Biên soạn chi tiết 12 archetype
    tiếng Việt trong `app/data/archetypes.py` (mỗi archetype: mô tả, 4-5 điểm mạnh,
    watchouts, nên/không nên khi giao tiếp, động lực, hành vi khi stress, gợi ý cải
    thiện, độ phù hợp môi trường đại học) — **CẦN TRUNG REVIEW nội dung (core IP)**.
  - **Fusion engine** `app/services/epa/archetype.py`: deterministic scoring — DISC
    base +2, profile đảo +1, Mệnh +1, Tam hợp +1; hòa → DISC thắng. Không consent →
    DISC thuần. Narrative template + Claude API polish (ANTHROPIC_API_KEY, cache).
  - **Endpoint** GET /epa/candidates/{id}/archetype — Behavioural Layer (không cần
    Eastern toggle); chi tiết fusion chỉ hiện khi Eastern Layer bật.
  - **Đối chiếu contacts.csv** (2540 liên hệ, 281 email @hpu.edu.vn):
    scripts/update_contacts.py match tên không dấu → cập nhật **63/107 nhân sự**
    email thật + SĐT + địa chỉ (migration 0005 thêm address). 5 trùng tên +
    38 không có trong danh bạ → cần xử lý tay (danh sách in khi chạy script).
  - Backend 460 test pass, ruff sạch.
- Next: Trung review nội dung 12 archetype + xử lý tay 5+38 nhân sự chưa match;
  Sprint 7 frontend dashboard (màn archetype/EPA); điền ANTHROPIC_API_KEY để bật
  narrative polish.
