# DECISIONS — Architecture Decision Records (ADR)
# File: docs/DECISIONS.md

> Mỗi quyết định kiến trúc lớn ghi 1 entry theo format ADR.
> Thứ tự: ADR mới nhất ở đầu file.

---

## ADR-008: Gộp pipeline 8→5 trạng thái (Tiếp nhận / Đánh giá / Phỏng vấn)

**Status:** Accepted
**Date:** 2026-07-12
**Decided by:** Trung (quyết định) — Claude Code (triển khai)

### Context

Pipeline 8 trạng thái (ADR-001; nới REJECTED ở ADR-007) bị đánh giá quá dài. Trung yêu cầu
"quy trình gọn hơn": gộp Mới+Sàng lọc, Đã gửi test+Xong test, Phỏng vấn+Quyết định.

### Decision

1. PIPELINE_STAGES còn 5: `RECEIVED (Tiếp nhận)`, `ASSESSMENT (Đánh giá)`, `INTERVIEW (Phỏng vấn)`,
   `HIRED (Đã tuyển)`, `REJECTED (Từ chối)`. Ánh xạ gộp:
   - RECEIVED = NEW + SCREENING
   - ASSESSMENT = TEST_SENT + TEST_DONE
   - INTERVIEW = INTERVIEW + DECISION
2. Luồng TIẾN tuần tự `RECEIVED → ASSESSMENT → INTERVIEW`; từ INTERVIEW rẽ HIRED/REJECTED.
   Giữ ADR-007: REJECTED chuyển tới được từ mọi bước chưa kết thúc. HIRED chỉ vào từ INTERVIEW.
3. Gửi bài test DISC cho phép ở RECEIVED (tự chuyển ASSESSMENT) hoặc ASSESSMENT (gửi lại).
   Nộp bài KHÔNG còn tự đổi trạng thái (trước: TEST_SENT→TEST_DONE) — "đã làm test" tra theo
   `TestSession.completed_at`, không theo bước pipeline nữa (vì đã gộp).
4. Migration 0009 remap hồ sơ cũ theo bảng ánh xạ (chỉ UPDATE — `pipeline_stage` là String
   validate ở tầng app, không phải enum DB nên không đổi schema).

### Consequences

- (+) Ít bước, thao tác gọn; "từ chối mọi bước" vẫn giữ.
- (−) Mất phân biệt "đã gửi test" vs "đã nộp" ở tầng pipeline; nay tra theo TestSession (màn
  chi tiết vẫn hiện đủ kết quả; danh sách hiển thị trạng thái DISC ở mức gộp "Đánh giá").
- (−) Thay đổi phá vỡ dữ liệu → BẮT BUỘC chạy migration 0009 khi deploy.

### Alternatives considered

1. Giữ 8 bước (ADR-007): Trung thấy còn rườm rà — loại.
2. Chỉ gộp bước test: không đúng yêu cầu gộp cả 3 cặp.

### References

- ADR-001, ADR-007; `models/candidate.py`, `services/candidate_service.py`,
  `routers/test_links.py`, `routers/public_tests.py`, `frontend/src/lib/types.ts`, migration `0009`

---

## ADR-007: Nới pipeline — cho phép Từ chối (REJECTED) ở bất kỳ bước

**Status:** Accepted
**Date:** 2026-07-11
**Decided by:** Trung (quyết định) — Claude Code (đề xuất + triển khai)

### Context

Critical Business Rule gốc (ADR-001 / CLAUDE.md): pipeline ứng viên đi TUẦN TỰ nghiêm ngặt
`NEW → SCREENING → TEST_SENT → TEST_DONE → INTERVIEW → DECISION → HIRED/REJECTED`, chỉ được rẽ
REJECTED ở bước DECISION. Thực tế tuyển dụng: nhiều hồ sơ cần loại NGAY từ sớm (sai vị trí,
trượt sàng lọc, ứng viên rút hồ sơ) mà không có lý do bắt đi qua đủ TEST/INTERVIEW rồi mới loại
được. PLAN.md (standup 2026-07-03) đã ghi nhận điểm vướng này và hoãn chờ Trung quyết. Phản hồi
Trung 2026-07-11 ("quy trình tuyển dụng cần gọn hơn") → chốt nới "Từ chối ở bất kỳ bước".

### Decision

1. `get_allowed_next_stages` bổ sung `REJECTED` vào tập cho phép của MỌI trạng thái chưa kết
   thúc (NEW, SCREENING, TEST_SENT, TEST_DONE, INTERVIEW). DECISION giữ nguyên (HIRED/REJECTED).
   → Từ mỗi bước: đi TIẾN đúng 1 bước kế, HOẶC chuyển thẳng REJECTED.
2. GIỮ NGUYÊN các ràng buộc khác: không nhảy cóc TIẾN (vd NEW→INTERVIEW vẫn 422), không đi
   LÙI, không rời trạng thái kết thúc (HIRED/REJECTED). Chỉ mở đúng nhánh REJECTED.
3. Không nới HIRED sớm — chỉ vào HIRED từ DECISION (tuyển thật vẫn phải qua quyết định).
4. Đồng bộ 2 nơi đang lặp logic: backend `candidate_service.get_allowed_next_stages` và
   frontend `lib/types.ts nextStages()` (giữ nguyên PIPELINE_STAGES/TERMINAL_STAGES — không
   đụng model/migration).

### Rationale

1. REJECTED là hành vi "kết thúc sớm" tự nhiên, không phá tính tuần tự của luồng TIẾN.
2. Chỉ mở đúng 1 nhánh (REJECTED); HIRED vẫn bị canh qua DECISION → rủi ro nghiệp vụ thấp.
3. Không sửa model/migration → thay đổi nhỏ; test cũ (không-nhảy-cóc, không-đi-lùi,
   terminal-bất-động) vẫn xanh, chỉ thêm test cho nhánh REJECTED mới.

### Consequences

**Positive:**
- HR loại hồ sơ 1 chạm từ bất kỳ bước — đúng nhu cầu "gọn hơn".
- Thay đổi tối thiểu, giữ nguyên các bảo vệ tuần tự còn lại.

**Negative:**
- Logic pipeline vẫn bị lặp ở BE + FE (nợ kỹ thuật cũ); lần này sửa cả hai. Nếu còn nới thêm
  nên gom về 1 nguồn (BE trả `allowed_next` cho FE dùng, bỏ hằng số lặp).
- Chưa lưu "lý do từ chối" theo bước (chỉ đổi trạng thái) — cân nhắc bổ sung sau nếu cần thống kê.

### Alternatives considered

1. Gộp/bỏ bước TEST (TEST_SENT+TEST_DONE) hoặc cho nhảy bước tiến: Trung KHÔNG chọn (giữ luồng
   test tuần tự) — chỉ lấy "Từ chối mọi bước".
2. Pipeline tự do (any→any): quá lỏng, mất kiểm soát thứ tự — loại.

### References

- ADR-001, CLAUDE.md "Critical Business Rules" (dòng pipeline), PLAN.md standup 2026-07-03
- `backend/app/services/candidate_service.py`, `frontend/src/lib/types.ts`, `tests/test_candidates.py`

---

## ADR-006: Resolve tenant trên domain chính bằng "Mã tổ chức" (header X-Org-Slug)

**Status:** Accepted
**Date:** 2026-07-08
**Decided by:** Trung

### Context

Go-live HPU chạy trên **domain phẳng `hr.hpu.edu.vn`** (không dựng subdomain riêng cho từng
tenant). Kiến trúc gốc (ADR-003) resolve `organization_id` theo thứ tự: JWT claim → subdomain
`{slug}.BASE_DOMAIN` → header `X-Org-Slug` (CHỈ bật ở `is_development`). Trên `hr.hpu.edu.vn`
KHÔNG có subdomain nên với login (chưa có JWT) và các server-side fetch (career page) thì org
không thể resolve nếu chạy đúng production. Thực tế "đang chạy được" chỉ vì một **bug**:
`docker-compose.yml` set `ENV=production` trong khi `config.py` đọc `APP_ENV` → `APP_ENV` giữ
default `development` → `is_development=True` vô tình trên production (kéo theo lộ đường tắt dev).

### Decision

1. **`X-Org-Slug` ("Mã tổ chức") là cơ chế resolve tenant CHÍNH THỨC trên domain chính**, honor
   ở MỌI môi trường — nhưng CHỈ là **fallback** sau JWT (1) và subdomain (2), không override được
   tenant context đã xác định. Header chỉ CHỌN tổ chức để đăng nhập, không cấp quyền.
2. **Sửa bug môi trường**: truyền `APP_ENV=${APP_ENV:-production}` vào container backend/worker
   (không dùng biến `ENV` sai tên) → production chạy đúng chế độ.
3. **Mô hình domain**: `hr.hpu.edu.vn` = app admin + đăng nhập; `{slug}.hr.hpu.edu.vn` = career
   page công khai theo tenant. Giai đoạn HPU-only chỉ cần thêm block Caddy `hpu.hr.hpu.edu.vn`
   (KHÔNG cần wildcard). Khi mở đa tenant (SaaS) mới cần wildcard `*.hr.hpu.edu.vn` + TLS.

### Rationale

1. Header chỉ là bộ chọn org; xác thực vẫn bắt buộc credential hợp lệ → không phải backdoor.
2. Là fallback sau JWT + subdomain nên tenant subdomain / phiên đã đăng nhập luôn thắng — không
   thể dùng header để nhảy tenant khi context đã có.
3. Rủi ro còn lại chỉ là dò slug tồn tại (enumeration) — thấp, vì slug đã công khai trong URL
   career page; login luôn trả thông báo chung ("Email hoặc mật khẩu không đúng").
4. Bỏ phụ thuộc `is_development` cho luồng tenant → không còn cám dỗ ép prod chạy như dev.

### Consequences

**Positive:**
- Login + career page hoạt động đúng trên domain phẳng ở production, không phụ thuộc bug env.
- Đóng lỗ hổng "production chạy chế độ development" (lộ `/docs`, đường tắt dev).

**Negative:**
- Một header do client gửi tham gia chọn tenant — chấp nhận có kiểm soát (fallback + auth gate),
  cần nêu rõ khi chạy `/security-review`.
- Khi lên đa tenant thật cần bổ sung wildcard DNS/TLS và cân nhắc rate-limit/ghi log theo org.

### Alternatives considered

1. **Subdomain per-tenant cho cả app admin** (`hpu.hr.hpu.edu.vn` để đăng nhập): cần wildcard
   DNS/TLS ngay, thừa cho giai đoạn chỉ có HPU — hoãn tới khi mở SaaS.
2. **Giữ `X-Org-Slug` dev-only + ép `APP_ENV=development` ở prod**: sai bản chất, mở toàn bộ
   đường tắt dev trên production — loại.

### References

- ADR-003 (Multi-tenant isolation 3 lớp), `backend/app/middleware/tenant.py`
- `docker-compose.yml`, `.env.production.example`, `docs/DEPLOY.md`

---

## ADR-005: 12 Personality Archetype — fusion DISC + Mệnh + Tam hợp bằng scoring xác định

**Status:** Accepted
**Date:** 2026-07-05
**Decided by:** Trung (cung cấp tài liệu nguồn) — Claude Code (thiết kế mapping)

### Context

Critical Business Rules: "12 Personality Archetype = fusion DISC (16 profile) + Mệnh (5 hành)
+ Tam hợp (4 nhóm) + narrative". Trung cung cấp tài liệu DISC chi tiết
(`docs/DISC-Tieng-Viet.pdf` — báo cáo DISCstyles 40 trang tiếng Việt) làm nguồn nội dung
mô tả archetype. Cần thuật toán fusion XÁC ĐỊNH (deterministic, test được), không dựa vào
LLM để chọn archetype.

### Decision

1. **Base mapping DISC 16 profile → 12 archetype** (bảng trong `app/data/archetypes.py`):
   D→CHALLENGER, D/I→CATALYST, D/S→EXECUTOR, D/C→STRATEGIST, I→CONNECTOR,
   I/D→VISIONARY, I/S→MENTOR, I/C→VISIONARY, S→HARMONIZER, S/D→BUILDER, S/I→MENTOR,
   S/C→GUARDIAN, C→ANALYST, C/D→STRATEGIST, C/S→CRAFTSMAN, C/I→CRAFTSMAN.
2. **Fusion scoring**: base archetype +2 điểm; archetype của profile đảo (secondary/primary)
   +1; Mệnh +1 cho 2 archetype cùng hành (Kim: STRATEGIST/CRAFTSMAN, Mộc: BUILDER/MENTOR,
   Thủy: CONNECTOR/ANALYST, Hỏa: CATALYST/CHALLENGER, Thổ: GUARDIAN/HARMONIZER);
   Tam hợp +1 cho 3 archetype cùng nhóm (Thân-Tý-Thìn: VISIONARY/STRATEGIST/ANALYST,
   Dần-Ngọ-Tuất: CHALLENGER/EXECUTOR/CATALYST, Tỵ-Dậu-Sửu: CRAFTSMAN/GUARDIAN/BUILDER,
   Hợi-Mão-Mùi: MENTOR/HARMONIZER/CONNECTOR). Điểm cao nhất thắng; hòa → base DISC thắng.
   → Eastern data chỉ XÔ ĐẨY được kết quả khi cả Mệnh + Tam hợp cùng chỉ về hướng khác.
3. **Không có dữ liệu sinh/consent** → archetype tính từ DISC thuần (Behavioural Layer
   vẫn hoạt động đầy đủ — đúng rule Eastern Layer là toggle riêng).
4. **Narrative**: sinh từ template tiếng Việt (nội dung archetype + điểm DISC); nếu có
   `ANTHROPIC_API_KEY` thì gọi Claude API polish (best-effort, lỗi → dùng template),
   cache theo hash input (Redis 30 ngày trên production — risk #4 HUONG-DAN).
5. **Nội dung 12 archetype** biên soạn từ `docs/DISC-Tieng-Viet.pdf` (Trung cung cấp
   2026-07-05) — cần Trung review nội dung trước go-live vì đây là core IP.

### Consequences

- (+) Deterministic, test được từng nhánh fusion; không phụ thuộc LLM để phân loại.
- (+) Ứng viên không consent vẫn có archetype (DISC-only) — đúng luật + đúng business rule.
- (−) Mapping 16→12 có chủ đích để một số profile chia sẻ archetype — nếu Trung muốn
  mapping khác chỉ cần sửa bảng trong `app/data/archetypes.py` (test parity mapping đi kèm).

---

## ADR-004: Google OAuth qua ID token verification, phân quyền theo Workspace domain của tenant

**Status:** Accepted
**Date:** 2026-07-03
**Decided by:** Trung (yêu cầu) — Claude Code (thiết kế)

### Context

Yêu cầu: (1) tài khoản quản lý/sử dụng đăng nhập bằng Google theo domain `hpu.edu.vn`;
(2) ứng viên đăng nhập bằng tài khoản Google bất kỳ. Hệ thống multi-tenant nên mỗi tenant
có thể có Workspace domain riêng (HPU = hpu.edu.vn, tenant khác = domain khác).

### Decision

1. **Frontend dùng Google Identity Services (GIS)** lấy `id_token`, gửi về backend —
   backend KHÔNG làm OAuth redirect flow (không cần lưu client_secret cho flow này).
2. **Backend verify id_token** qua endpoint `https://oauth2.googleapis.com/tokeninfo`
   (kiểm `aud` = GOOGLE_CLIENT_ID, `email_verified`, `exp` do Google check) — đủ an toàn
   cho quy mô hiện tại, không thêm dependency `google-auth`.
3. **Staff (`POST /api/v1/auth/google`)**: bắt buộc có tenant context; domain email phải khớp
   `organization.settings.google_workspace_domain` (per-tenant, HPU = hpu.edu.vn).
   User đã tồn tại → đăng nhập; chưa tồn tại và domain khớp → auto-provision với
   `org_role=member` (quyền thấp nhất, admin nâng quyền sau). Tắt auto-provision bằng
   `settings.google_auto_provision=false`.
4. **Ứng viên (`POST /api/v1/public/auth/google`)**: Google bất kỳ (email đã verify),
   find-or-create `Candidate` theo email trong tenant, cấp JWT riêng `type=candidate`
   TTL 60 phút — KHÔNG dùng chung token với staff (không có org_role, không vào được
   API quản trị).
5. Login mật khẩu giữ nguyên làm fallback (dev, tenant chưa có Workspace).

### Consequences

- (+) Mỗi tenant tự cấu hình domain; thêm tenant mới không đổi code.
- (+) Candidate token tách biệt hoàn toàn khỏi staff token — giảm bề mặt tấn công.
- (−) Gọi Google tokeninfo mỗi lần login (thêm ~100ms); chấp nhận được, có thể chuyển
  sang verify chữ ký local (google-auth + cached certs) khi lưu lượng tăng.
- (−) Cần cấu hình `GOOGLE_CLIENT_ID` trong env cả backend lẫn frontend
  (`NEXT_PUBLIC_GOOGLE_CLIENT_ID`); chưa cấu hình → endpoint trả lỗi nghiệp vụ rõ ràng.

### Alternatives considered

1. **OAuth authorization-code flow đầy đủ ở backend**: an toàn tương đương với ID token
   cho mục đích authentication thuần, nhưng phức tạp hơn (redirect, state, client_secret) — loại.
2. **Thư viện `google-auth` verify chữ ký local**: nhanh hơn nhưng thêm dependency và cache
   certs; để dành khi scale — chưa cần.

---

## ADR-003: Multi-tenant theo Shared Schema + PostgreSQL RLS (không schema-per-tenant)

**Status:** Accepted
**Date:** 2026-04-18
**Decided by:** Trung

### Context

TalentChart phục vụ nhiều trường ĐH/HR agency trên cùng một hệ thống. Cần chọn mô hình multi-tenant: schema riêng cho từng tenant (schema-per-tenant), database riêng, hay shared schema với cột `organization_id`.

### Decision

Dùng **Shared Schema (Pooled)** — mọi tenant chung 1 schema, phân tách bằng cột `organization_id NOT NULL` trên mọi bảng tenant-scoped, bảo vệ 3 lớp: `TenantMiddleware` (resolve org_id từ JWT/subdomain/header dev) → SQLAlchemy event listener tự động filter query (`with_loader_criteria`) → PostgreSQL Row Level Security làm safety-net cuối. Cross-tenant access luôn trả 404, không 403 (tránh lộ sự tồn tại của resource).

### Rationale

1. Team nhỏ (1 mid dev + 2 intern) — schema-per-tenant tốn công vận hành migration N lần cho N tenant.
2. Chi phí hạ tầng thấp hơn nhiều so với database-per-tenant khi số lượng khách hàng mục tiêu Phase 1-2 chỉ 10-50.
3. RLS ở tầng PostgreSQL là lớp phòng thủ cuối cùng nếu lớp middleware/ORM có bug — giảm rủi ro "1 bug leak tenant = giết startup".
4. Dễ dàng thêm composite index có `organization_id` ở đầu để tối ưu query theo tenant.

### Consequences

**Positive:**
- Vận hành/migration đơn giản, 1 lần deploy cho mọi tenant.
- Chi phí hạ tầng thấp, phù hợp giai đoạn early-stage.

**Negative:**
- Rủi ro data leak nếu 1 trong 3 lớp bảo vệ bị bỏ sót ở 1 query mới — bắt buộc phải có `test_tenant_isolation.py` cho mọi module và chạy `/security-review` trước mỗi lần merge/deploy.
- Khó tách riêng tài nguyên (CPU/IO) cho 1 tenant lớn nếu sau này có khách hàng cần cô lập hoàn toàn — sẽ cân nhắc lại khi MRR đạt mốc scale Phase 3-4.

### Alternatives considered

1. **Schema-per-tenant**: cô lập tốt hơn nhưng migration phải chạy N lần, phức tạp khi N tăng — loại vì team quá nhỏ để vận hành.
2. **Database-per-tenant**: cô lập cao nhất nhưng chi phí hạ tầng và vận hành quá lớn so với quy mô 10-50 khách hàng ban đầu — loại.

### References

- TalentChart_Architecture_Phase12 — mục Multi-tenant Architecture
- `~/hpu-dev/skills/multi-tenant-saas/SKILL.md`
- `.claude/rules/tenant-isolation.md`

---

## ADR-002: Chốt stack FastAPI (Python) + Next.js 15, không dùng NestJS

**Status:** Accepted
**Date:** 2026-04-15
**Decided by:** Trung

### Context

Bản Concept_Roadmap ban đầu (tầm nhìn 18 tháng) phác thảo stack NestJS + PostgreSQL + pgvector. Khi lập kế hoạch triển khai thực tế 9 tháng (Strategy_Phase12/Architecture_Phase12), team chỉ có 1 mid dev + 2 intern CNTT, cần chọn lại stack cụ thể để build.

### Decision

Chốt dùng **FastAPI (Python 3.12, async) cho backend + Next.js 15 App Router cho frontend**, thay vì NestJS. Đây là stack chính thức trong CLAUDE.md và toàn bộ skill/slash-command của hpu-dev framework.

### Rationale

1. Python có hệ sinh thái mạnh cho phần tính toán EPA Engine (lịch âm, ngũ hành) và dễ gọi Anthropic API (`anthropic` SDK chính thức hỗ trợ tốt Python).
2. Đồng bộ với framework phát triển chung `hpu-dev` của HPU AI Lab (các project nội bộ khác cũng dùng FastAPI) — dev/intern không phải học 2 stack khác nhau.
3. FastAPI + Pydantic v2 phù hợp với triết lý "vibe coding" — Claude Code sinh code CRUD/schema rất nhất quán trên stack này (đã có sẵn skill `fastapi-crud`, `epa-engine`).
4. Next.js 15 App Router có sẵn pattern subdomain routing (middleware.ts) cần thiết cho public career page theo tenant.

### Consequences

**Positive:**
- Tận dụng toàn bộ tooling/skill/slash-command có sẵn của hpu-dev (không phải viết mới).
- 1 ngôn ngữ backend (Python) cho cả EPA Engine lẫn CRUD nghiệp vụ.

**Negative:**
- Bỏ qua kinh nghiệm NestJS nếu có sẵn trong team (không đáng kể vì team mới).
- Tài liệu Concept_Roadmap gốc (NestJS) không còn khớp 100% với triển khai thực tế — cần đọc Architecture_Phase12/Strategy_Phase12 làm nguồn chính thức, Concept_Roadmap chỉ còn giá trị tham khảo tầm nhìn dài hạn.

### Alternatives considered

1. **NestJS + TypeScript full-stack**: đồng bộ ngôn ngữ FE/BE nhưng hệ sinh thái tính toán lịch âm/ngũ hành yếu hơn Python, và không khớp hpu-dev framework hiện có — loại.
2. **Django**: mature nhưng nặng, không async-first bằng FastAPI, không hợp mô hình EPA Engine cần async gọi Claude API — loại.

### References

- TalentChart_Strategy_Phase12, TalentChart_Architecture_Phase12 (v2.0, tháng 4/2026)
- `CLAUDE.md` (Tech Stack)

---

## ADR-001: Build mới hoàn toàn, KHÔNG migrate code

**Status:** Accepted
**Date:** 2026-04-10
**Decided by:** Trung

### Context

Có 2 codebase nguồn (SmartHire + Fortune HR) đã chạy production cho HPU. Câu hỏi: migrate sang TalentChart hay build mới với AI tạo sinh?

### Decision

Build mới hoàn toàn bằng Claude Code ("vibe coding"). Kế thừa thuật toán + dữ liệu từ codebase cũ qua "knowledge transfer" (port logic LunarData/Can Chi, DISC scoring) bằng slash-command `/epa-port`, KHÔNG copy nguyên code.

### Rationale

1. Vibe coding với AI nhanh hơn migrate + refactor multi-tenant từ code single-tenant cũ.
2. Code cũ (SmartHire, Fortune HR) là single-tenant — refactor thành multi-tenant sẽ để lại nhiều technical debt.
3. Build mới cho phép thiết kế clean architecture đúng chuẩn hpu-dev (TenantScopedBase, RLS...) ngay từ đầu.
4. Team (mid dev + 2 intern) xây dựng năng lực thực sự qua quá trình viết mới thay vì đọc hiểu code cũ.

### Consequences

**Positive:**
- Codebase sạch, đồng nhất pattern multi-tenant ngay từ commit đầu tiên.
- Tốc độ phát triển phù hợp với đội hình 1 mid dev + 2 intern.

**Negative:**
- Rủi ro bug trong port logic bát tự/Can Chi — mitigate bằng bộ test so khớp ≥20 case với output hệ cũ khi chạy `/epa-port`.
- Vibe coding có thể sinh lỗ hổng bảo mật — mitigate bắt buộc bằng `/security-review` trước mỗi lần merge.

### Alternatives considered

1. **Migrate SmartHire + refactor multi-tenant**: tốn thời gian, để lại nhiều nợ kỹ thuật — loại.
2. **Hybrid (giữ SmartHire ATS, chỉ build mới EPA)**: phải bảo trì song song 2 stack, tốn gấp đôi công sức — loại.

### References

- TalentChart_Concept_Roadmap, TalentChart_Strategy_Phase12
