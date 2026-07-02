# Hướng dẫn triển khai TalentChart bằng Claude Code

> File này là kim chỉ nam thực thi — đọc cùng với `CLAUDE.md` (quy ước dự án), `docs/PLAN.md` (sprint hiện tại) và `docs/DECISIONS.md` (các quyết định kiến trúc đã chốt).

## 0. Lưu ý quan trọng về nguồn tài liệu

Bộ 4 tài liệu gốc có một điểm lệch: `TalentChart_Concept_Roadmap` mô tả tầm nhìn 18 tháng/4 phase với stack NestJS; còn `TalentChart_Strategy_Phase12` và `TalentChart_Architecture_Phase12` (bản mới hơn, v2.0 tháng 4/2026) đã **chốt kế hoạch triển khai thực tế**: 9 tháng/2 phase, stack FastAPI + Next.js. Hướng dẫn này và toàn bộ scaffold trong thư mục `talentchart/` đi theo **Strategy + Architecture** vì đó là bản triển khai gần nhất, chi tiết nhất. `Concept_Roadmap` chỉ còn giá trị tham khảo tầm nhìn dài hạn (Phase 3-4: mobile, B2C, MRR 1 tỷ).

## 1. Những gì đã được chuẩn bị sẵn

Thư mục `talentchart/` (cùng cấp với `hpu-dev/`) đã được scaffold theo đúng chuẩn hpu-dev v2.0, loại `--type=saas`, port `8003`:

```
talentchart/
├── CLAUDE.md                 ← đã điền Project Overview + Critical Business Rules thật của TalentChart
├── docs/
│   ├── PLAN.md               ← đã điền sẵn Sprint 1 (Foundation) chi tiết
│   ├── DECISIONS.md          ← đã có 3 ADR nền tảng (build-mới, chọn stack, chọn multi-tenant RLS)
│   └── HUONG-DAN-TRIEN-KHAI-CLAUDE-CODE.md   ← chính là file này
├── .claude/
│   ├── commands/              ← 7 slash-command (new-module, new-tenant, epa-port, security-review, review, deploy, add-export)
│   └── rules/                 ← 4 rule bắt buộc (api-response, money-integer, soft-delete, tenant-isolation)
├── backend/app/{models,schemas,routers,services,middleware,core,tasks}/  ← khung thư mục FastAPI rỗng
├── backend/app/services/epa/  ← nơi sẽ chứa lunar.py, canchi.py, menh.py, tamhop.py, compatibility.py, archetype.py, narrative.py
├── backend/alembic/versions/, backend/tests/
├── frontend/src/{app,components,lib,hooks,types,stores}/  ← khung Next.js 15
├── legacy/{smarthire-html,fortune-hr}/  ← ĐANG RỖNG, cần copy code nguồn vào đây (xem mục 6)
├── docker-compose.yml, backend/Dockerfile, frontend/Dockerfile
├── backend/pyproject.toml, frontend/package.json
├── .env.example
└── scripts/backup.sh
```

Những phần **chưa** có sẵn và Claude Code sẽ sinh ra trong quá trình build: toàn bộ code Python/TypeScript thực tế (`main.py`, models, routers...), migration Alembic, test.

## 2. Chuẩn bị môi trường (làm 1 lần, trên máy dev/server thật — không phải trong sandbox này)

```bash
# 1. Cài Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 2. Copy toàn bộ hpu-dev/ (đã có sẵn trong thư mục bạn kết nối) lên máy dev, rồi:
cd ~/hpu-dev
chmod +x setup.sh new-project.sh
./setup.sh
# → tạo ~/hpu-dev/, cài 7 skill vào ~/.claude/skills/, tạo ~/.claude/CLAUDE.md (global),
#   tạo Docker network "caddy-proxy"

# 3. Copy thư mục talentchart/ (đã scaffold sẵn) vào đúng vị trí ~/hpu-dev/talentchart
#    (new-project.sh vốn tạo project tại đây, nên hãy đặt đúng chỗ để các đường dẫn tương đối
#    trong CLAUDE.md / skill (~/hpu-dev/...) hoạt động đúng)

# 4. Khởi tạo git thật (bản scaffold trong sandbox không tạo được git do giới hạn quyền ổ đĩa mounted)
cd ~/hpu-dev/talentchart
git init
git add -A
git commit -m "chore: initial scaffold from hpu-dev v2.0 (type=saas)"

# 5. Tạo file .env từ .env.example và điền giá trị thật
cp .env.example .env
nano .env   # điền DB_PASSWORD, REDIS_PASSWORD, JWT_SECRET (random dài), ANTHROPIC_API_KEY, MINIO_*, SMTP_*...

# 6. Cài công cụ dev
# Python: cài uv (https://docs.astral.sh/uv/) — backend dùng uv thay pip
curl -LsSf https://astral.sh/uv/install.sh | sh
# Node: cài pnpm cho frontend
npm install -g pnpm
```

Kiểm tra `claude --version` và `docker compose version` chạy được trước khi qua bước 3.

## 3. Mở Claude Code trong project

```bash
cd ~/hpu-dev/talentchart
claude
```

Claude Code sẽ tự động đọc `CLAUDE.md` trong thư mục hiện tại (project instructions) cộng với `~/.claude/CLAUDE.md` (global rules chung của HPU) và tự nhận diện 7 skill trong `~/.claude/skills/` dựa trên từ khoá xuất hiện trong hội thoại (ví dụ nhắc "multi-tenant" → tự load skill `multi-tenant-saas`; nhắc "bát tự"/"archetype" → tự load `epa-engine`).

Lệnh đầu tiên nên chạy (đúng như gợi ý mặc định của `new-project.sh` cho loại saas):

```
Đọc CLAUDE.md và docs/PLAN.md, setup skeleton: models/base.py với TenantScopedBase,
middleware tenant, organization model, user model, auth router.
Tuân thủ đúng docs/DECISIONS.md ADR-003 (shared schema + RLS).
```

## 4. Quy trình bắt buộc cho MỌI task (không được bỏ bước)

Đây là quy trình 6 bước từ Claude Code Playbook — áp dụng cho từng story trong `docs/PLAN.md`:

1. **UNDERSTAND** — Tự đọc kỹ yêu cầu/story trong PLAN.md, không hỏi AI trước khi bạn tự hiểu vấn đề.
2. **PLAN** — Nếu là feature lớn, brainstorm trên Claude.ai (có Project Knowledge chứa Architecture PDF, CLAUDE.md, api-conventions.md, db-conventions.md), chốt kế hoạch vào `docs/PLAN.md`. Quyết định kiến trúc lớn → viết ADR mới trong `docs/DECISIONS.md` TRƯỚC khi code.
3. **IMPLEMENT** — Dùng Claude Code CLI để sinh code, ưu tiên dùng slash-command có sẵn (mục 5) thay vì yêu cầu tự do.
4. **TEST** — Chạy `pytest`, sau đó bắt buộc chạy `/security-review` trên module vừa sửa.
5. **COMMIT** — Chỉ commit sau khi `/review` sạch. Dùng Conventional Commits (`feat:`, `fix:`, `chore:`...).
6. **PR** — Tạo PR với checklist 4 nhóm (multi-tenant / security / code quality / docs), Trung review trước khi merge vào `main`.

## 5. Slash-command đã cài sẵn — dùng khi nào

| Lệnh | Dùng khi nào trong TalentChart |
|---|---|
| `/new-module {entity}` | Mỗi khi cần thêm 1 entity CRUD mới, ví dụ `/new-module candidate`, `/new-module job_post`, `/new-module interview_score`. Claude tự sinh model/schema/router/service/migration/test theo chuẩn multi-tenant. |
| `/new-tenant {slug}` | Tạo tổ chức mới, ví dụ `/new-tenant hpu` (khách hàng số 0), sau này `/new-tenant dhbk-hcm` khi onboard trường tiếp theo ở Phase 2. |
| `/epa-port {module}` | Port từng phần EPA Engine, dùng lần lượt: `/epa-port lunar`, `/epa-port canchi`, `/epa-port menh`, `/epa-port tamhop`, `/epa-port compatibility`, `/epa-port team-suggest`. **Bắt buộc có code JS gốc trong `legacy/fortune-hr/` trước** (xem mục 6). |
| `/security-review [file\|--pr]` | Chạy sau MỌI module liên quan tenant/auth/EPA, và bắt buộc trước `/deploy`. |
| `/review` | Chạy trước khi commit, chấm điểm 7 tiêu chí HPU (API/DB/Security/UI/Code quality/Docker/Docs). |
| `/deploy` | Chạy khi đã sẵn sàng lên staging/production — quy trình 7 bước có pre-flight check + rollback. |
| `/add-export {entity}` | Thêm khi cần xuất Excel, ví dụ `/add-export candidate` cho báo cáo danh sách ứng viên. |

## 6. Chuẩn bị dữ liệu để port EPA Engine

Module EPA (bát tự/Can Chi/archetype) là USP kỹ thuật cốt lõi, phải **port nguyên xi** từ Fortune HR — không được để AI "cải tiến" thuật toán. Trước khi chạy `/epa-port`:

1. Copy toàn bộ code nguồn Fortune HR (đặc biệt `server.js` chứa `LunarData`, hàm tính Can Chi/Nạp Âm/Mệnh) vào `legacy/fortune-hr/` trong project.
2. Copy code DISC scoring từ SmartHire vào `legacy/smarthire-html/` nếu cần đối chiếu.
3. Chạy `/epa-port lunar` trước tiên — đây là module nền cho mọi tính toán khác, có bug-fix quan trọng đã biết: phải dùng **năm âm lịch** (không phải năm dương lịch) khi tính Can Chi cho người sinh trước Tết. Test bắt buộc: `get_canchi_from_birth(1,1,1938)` phải ra "Đinh Sửu" (ứng năm 1937 âm lịch), không phải "Mậu Dần".
4. Sau mỗi lần port, chạy bộ test so khớp ≥20 case với output của code JS gốc. Nếu lệch kết quả, đó là **lỗi port** (thường do sao chép nhầm hằng số) — sửa code Python, tuyệt đối không sửa công thức.
5. Riêng nội dung mô tả của 12 Personality Archetype (STRATEGIST, VISIONARY, BUILDER, EXECUTOR, CONNECTOR, CATALYST, HARMONIZER, GUARDIAN, ANALYST, CRAFTSMAN, MENTOR, CHALLENGER) là do Trung viết tay — AI chỉ polish câu chữ, không tự sáng tác.

## 7. Lộ trình 8 sprint Phase 1 (4 tháng — theo Strategy_Phase12)

Dùng bảng này để cập nhật `docs/PLAN.md` mỗi 2 tuần (1 sprint):

| Sprint | Nội dung chính | Slash-command chủ đạo |
|---|---|---|
| 1 (đã lên kế hoạch sẵn trong `docs/PLAN.md`) | Foundation: multi-tenant, auth, RLS | — (code nền, chưa cần slash-command) |
| 2-3 | Module ATS Core: candidates/campaigns, port DISC test từ SmartHire | `/new-module candidate`, `/new-module campaign` |
| 4 | Job Board + Career Page công khai theo tenant | `/new-module job_post`, cấu hình `middleware.ts` subdomain routing |
| 5 | Port EPA Engine (lunar/canchi/menh/tamhop/compatibility/team-suggest) | `/epa-port {module}` |
| 6 | Fusion 12 Archetype + AI narrative qua Claude API | code thủ công + review kỹ (core IP) |
| 7 | Hoàn thiện frontend + Dashboard | `/new-module` cho các entity còn thiếu, `hpu-ui`/`nextjs-admin` skill tự hỗ trợ |
| 8 | Import dữ liệu từ hệ cũ + Cutover go-live cho HPU | `/deploy`, script `scripts/migrate-from-*.py` (tự viết riêng cho lần cutover) |

Sau Sprint 8 là go-live production cho HPU (khách hàng số 0), sau đó bước sang Phase 2 (Go-to-market, 5 tháng, thêm Sale Rep/CSM, mục tiêu 50 paying customers, MRR ~1 tỷ/tháng).

## 8. Việc KHÔNG nên giao cho AI tự làm

Theo Claude Code Playbook, những việc sau cần Trung tự làm hoặc kiểm soát chặt, không để Claude Code tự quyết:

- Code xử lý thanh toán (payment)
- Cryptographic primitives (tự chọn thuật toán mã hoá)
- Migration dữ liệu production thật (chỉ chạy sau khi đã test kỹ trên staging)
- Quản lý secret (JWT_SECRET, API key...)
- Nội dung tuân thủ pháp lý (Nghị định 13/2023/NĐ-CP)
- Nội dung gốc của 12 Personality Archetype (core IP — Trung viết tay)

## 9. Trước khi deploy production — checklist bắt buộc

- [ ] `/security-review --pr` sạch, đặc biệt mục Multi-tenant safety (CRITICAL)
- [ ] `/review` đạt điểm tốt trên cả 7 tiêu chí
- [ ] `test_tenant_isolation.py` pass cho mọi module có dữ liệu tenant
- [ ] Coverage backend > 70% (KPI trong Strategy_Phase12)
- [ ] `.env.production` đã điền đủ, không secret nào có giá trị default/rỗng
- [ ] Đã backup database trước khi chạy migration (script `scripts/backup.sh`)
- [ ] Test trên staging trước, không deploy thẳng production
- [ ] Chạy `/deploy` (quy trình 7 bước có pre-flight check + rollback bằng `git reset --hard HEAD~1` nếu lỗi)

## 10. Rủi ro lớn nhất cần theo dõi liên tục

1. **Data leak giữa các tenant** — kiểm tra bằng `/security-review` sau mọi PR chạm vào query DB.
2. **EPA Engine sai kết quả so với Fortune HR gốc** — kiểm tra bằng bộ 100 test case so sánh (xem mục 6).
3. **Mid dev nghỉ giữa chừng** — vì vậy `CLAUDE.md`, `docs/PLAN.md`, `docs/DECISIONS.md` phải luôn được cập nhật đầy đủ để bất kỳ ai (kể cả intern) có thể tiếp tục.
4. **Chi phí Anthropic API tăng đột biến** (do gọi narrative EPA nhiều) — cache Redis 30 ngày cho kết quả narrative, giới hạn theo tier gói.

## 11. Tài liệu tham khảo đầy đủ

- `CLAUDE.md` — quy ước bắt buộc của project này
- `docs/PLAN.md` — sprint đang chạy
- `docs/DECISIONS.md` — ADR-001 (build mới), ADR-002 (chọn FastAPI+Next.js), ADR-003 (multi-tenant RLS)
- `~/hpu-dev/_shared/api-conventions.md`, `~/hpu-dev/_shared/db-conventions.md`
- `~/hpu-dev/skills/*/SKILL.md` — đặc biệt `multi-tenant-saas` và `epa-engine`
- 4 tài liệu gốc HPU AI Lab: TalentChart_Concept_Roadmap, TalentChart_Strategy_Phase12, TalentChart_Architecture_Phase12, TalentChart_Claude_Code_Playbook (trong thư mục gốc bạn đã kết nối)
