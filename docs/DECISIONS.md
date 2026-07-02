# DECISIONS — Architecture Decision Records (ADR)
# File: docs/DECISIONS.md

> Mỗi quyết định kiến trúc lớn ghi 1 entry theo format ADR.
> Thứ tự: ADR mới nhất ở đầu file.

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
