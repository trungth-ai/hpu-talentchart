# DEPLOY.md — Runbook triển khai & Cutover go-live HPU

> Quy trình theo `/deploy` + checklist HUONG-DAN §9. Người thực hiện: **Trung** (migration
> production KHÔNG giao AI — playbook §8).
> Server: HPU (Docker). Reverse proxy: **Caddy HỆ THỐNG của server** (không phải
> caddy-docker-proxy) — stack chỉ publish frontend ra host port, Caddy trỏ domain vào port đó.

## Mô hình domain (ADR-006)

| Domain | Vai trò | Caddy → |
|---|---|---|
| `hr.hpu.edu.vn` | App admin + đăng nhập staff (nhập **Mã tổ chức** = slug) | `localhost:3300` |
| `hpu.hr.hpu.edu.vn` | Career page công khai của tenant HPU | `localhost:3300` |

- Đăng nhập trên domain phẳng resolve tenant qua header `X-Org-Slug` = "Mã tổ chức" (ADR-006);
  KHÔNG cần subdomain riêng để login.
- **Giai đoạn HPU-only: KHÔNG cần wildcard.** Chỉ 2 record + 2 block Caddy ở trên.
- Khi mở đa tenant (SaaS) về sau: thêm wildcard DNS `*.hr.hpu.edu.vn` + TLS DNS-01
  (`CLOUDFLARE_API_TOKEN`) cho career page mỗi tenant.

---

## 0. Điều kiện tiên quyết (làm 1 lần)

- [ ] DNS: A record `hr.hpu.edu.vn` **và** `hpu.hr.hpu.edu.vn` trỏ về IP server (không wildcard)
- [ ] Block trong Caddyfile hệ thống của server:
  ```caddy
  hr.hpu.edu.vn {
      reverse_proxy localhost:3300
  }
  hpu.hr.hpu.edu.vn {
      reverse_proxy localhost:3300
  }
  ```
  → reload: `sudo systemctl reload caddy` (hoặc `caddy reload --config /etc/caddy/Caddyfile`)
- [ ] Google Cloud Console — OAuth Client ID (ADR-004):
  - Authorized JavaScript origins: `https://hr.hpu.edu.vn`
  - (Dev: thêm `http://localhost:3000`)
- [ ] `cp .env.production.example .env.production` và điền đủ — **không secret nào để rỗng**
  (đặc biệt `APP_DOMAIN=hr.hpu.edu.vn`, `FRONTEND_PORT=3300`, `JWT_SECRET`, `DB_PASSWORD`,
  `REDIS_PASSWORD`, `MINIO_ACCESS_KEY/SECRET_KEY`).

## 1. Pre-flight check (trên máy dev / CI — KHÔNG trên production)

```bash
# Backend (máy Windows dev KHÔNG có uv/docker → chạy thẳng venv)
backend/.venv/Scripts/python -m pytest --cov=app --cov-fail-under=70
backend/.venv/Scripts/python -m ruff check .
# Frontend
cd frontend && npm ci && npm run typecheck && npm run build
# CI GitHub Actions phải XANH trên nhánh sẽ deploy
```

Checklist bắt buộc trước khi deploy production (HUONG-DAN §9):
- [ ] `/security-review --pr` sạch — đặc biệt Multi-tenant safety (RLS migration 0001-0003)
      **và cơ chế X-Org-Slug ở ADR-006** (header chọn tenant — xác nhận vẫn là fallback + auth gate)
- [ ] `/review` đạt 7 tiêu chí
- [ ] `test_tenant_isolation.py` + toàn bộ suite pass
- [ ] Coverage > 70%
- [ ] Nội dung 12 Archetype đã được Trung review (core IP — ADR-005)

## 2. Lấy code + build (trên server)

```bash
# Lần đầu:
git clone https://github.com/trungth-ai/hpu-talentchart ~/hpu-dev/talentchart
cd ~/hpu-dev/talentchart
# Lần sau:
git pull origin main   # ⚠️ phải có commit vá "bake BACKEND_INTERNAL_URL" (273b225 trở đi)
```

> ✅ **Migration TỰ ĐỘNG (không cần chạy tay).** Service one-shot `migrate` trong
> `docker-compose.yml` chạy `alembic upgrade head` sau khi `db` healthy và **TRƯỚC** khi
> `backend`/`worker` khởi động (`condition: service_completed_successfully`). Vì vậy **luôn
> nhớ backup TRƯỚC khi `up`** (bước 3). Nếu migrate lỗi → backend KHÔNG khởi động (fail-fast,
> tránh chạy code mới trên schema cũ); xem log: `docker compose logs migrate`.
> Chạy migration độc lập khi cần: `docker compose --env-file .env.production run --rm migrate`.

> ⚠️ **BẪY THƯỜNG GẶP — proxy `/api` về `localhost:8003`.** Next.js **đóng băng rewrites lúc
> BUILD**, nên `BACKEND_INTERNAL_URL` phải đúng ở thời điểm build image frontend (đã set qua
> build ARG trong `frontend/Dockerfile` + `docker-compose.yml`). Nếu chạy image frontend CŨ
> (build trước bản vá) sẽ thấy log `Failed to proxy http://localhost:8003/... ECONNREFUSED` và
> UI báo "Không kết nối được máy chủ". Khắc phục: **build lại frontend**:
> ```bash
> docker compose --env-file .env.production build --no-cache frontend
> docker compose --env-file .env.production up -d frontend
> ```

## 3. Backup TRƯỚC khi `up` (bắt buộc mỗi lần deploy)

Vì migration tự chạy trong bước 4, backup phải làm TRƯỚC đó (db vẫn đang chạy từ lần deploy trước):

```bash
docker compose exec db pg_dump -U talentchart -F c talentchart > backups/pre-deploy-$(date +%Y%m%d-%H%M).dump
# Container backup tự chạy hằng ngày (scripts/backup-postgres.sh, giữ 14 ngày)
```

## 4. Khởi động đầy đủ + verify RLS

```bash
docker compose --env-file .env.production up -d --build
# Migration TỰ ĐỘNG chạy trong lệnh trên (service `migrate` → alembic upgrade head)
docker compose exec backend alembic current            # kỳ vọng: head hiện tại (0011)

# Verify RLS đã bật (lớp bảo vệ số 3):
docker compose exec db psql -U talentchart -c \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public' ORDER BY 1;"
# → users, campaigns, candidates, job_posts, test_sessions... đều rowsecurity = t
```

## 5. Khởi tạo dữ liệu HPU (cutover — chạy 1 lần duy nhất)

```bash
# 5.1 Tạo tenant HPU + tài khoản owner + bật Google Workspace domain
docker compose exec backend python scripts/create_tenant.py \
  --slug hpu --name "Trường Đại học Hải Phòng" \
  --email trungth@hpu.edu.vn --password "<mật-khẩu-mạnh>" \
  --google-domain hpu.edu.vn
# → Đăng nhập tại https://hr.hpu.edu.vn, ô "Mã tổ chức" nhập: hpu

# 5.2 Import 107 nhân sự từ file lương (đã có cơ sở đồng ý từ Fortune HR cũ)
docker cp "Luong T8.xlsx" talentchart-backend:/tmp/luong-t8.xlsx
docker cp contacts.csv talentchart-backend:/tmp/contacts.csv
docker compose exec backend python scripts/import_employees.py \
  --file /tmp/luong-t8.xlsx --org-slug hpu --with-epa-consent

# 5.3 Đối chiếu danh bạ → email thật + SĐT + địa chỉ (63/107 tự match)
docker compose exec backend python scripts/update_contacts.py \
  --csv /tmp/contacts.csv --org-slug hpu
# → Xử lý tay 5 người trùng tên + 38 người không có trong danh bạ (script in danh sách)

# 5.4 (Tùy chọn) Bật Eastern Layer cho HPU — hiện Can Chi/Mệnh/Tam hợp:
# docker compose exec db psql -U talentchart -c \
#   "SET app.current_org_id='<org-uuid>'; \
#    UPDATE organizations SET settings = settings || '{\"eastern_layer_enabled\": true}' WHERE slug='hpu';"
```

> ℹ️ Kiểm tra dữ liệu qua psql: bảng `users` bật **FORCE ROW LEVEL SECURITY** nên phải
> `SET app.current_org_id='<org-uuid>'` trong cùng phiên mới thấy row (deny-by-default).
> Lấy org-uuid: `SELECT id FROM organizations WHERE slug='hpu';`

## 6. Smoke test production

```bash
# Health (không cần tenant)
curl -f https://hr.hpu.edu.vn/health

# Login qua Mã tổ chức (header X-Org-Slug = slug) → 200 + token:
curl -X POST https://hr.hpu.edu.vn/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Org-Slug: hpu" \
  -d '{"email":"trungth@hpu.edu.vn","password":"<mật-khẩu>"}'

# Career page công khai tenant HPU:
curl -f https://hpu.hr.hpu.edu.vn
```

- [ ] Đăng nhập UI tại https://hr.hpu.edu.vn (Mã tổ chức: `hpu`) thành công
- [ ] Đăng nhập Google bằng tài khoản @hpu.edu.vn thật hoạt động
- [ ] Gửi 1 bài test DISC thật → làm bài → HR xem kết quả + archetype
- [ ] Case kiểm chứng EPA: Trần Hữu Nghị (1/1/1938) → Đinh Sửu
- [ ] Xác nhận CÔ LẬP TENANT: tạo org thử nghiệm thứ 2, đăng nhập bằng Mã tổ chức khác,
      xác nhận KHÔNG thấy dữ liệu HPU

## 7. Rollback (khi có sự cố)

```bash
git reset --hard HEAD~1 && docker compose --env-file .env.production up -d --build
# Nếu migration đã chạy và cần lùi:
docker compose exec backend alembic downgrade -1
# Khôi phục dữ liệu từ backup bước 3:
docker compose exec -T db pg_restore -U talentchart -d talentchart --clean < backups/pre-deploy-*.dump
```

## Theo dõi sau go-live (HUONG-DAN §10)

- Log tổng hợp: `docker compose logs -f frontend backend` (structlog JSON ở backend)
- Chi phí Anthropic API: narrative có cache — theo dõi usage console.anthropic.com
- Backup hằng ngày trong `./backups/` (container `talentchart-backup`, giữ 14 ngày)
- Mọi PR chạm query DB → `/security-review` trước merge

## Phụ lục — chuyển sang đa tenant (SaaS, làm sau)

Khi phục vụ nhiều tổ chức ngoài HPU:
1. DNS wildcard `*.hr.hpu.edu.vn` + block Caddy wildcard (TLS DNS-01, cần `CLOUDFLARE_API_TOKEN`).
2. Mỗi tenant tạo bằng `scripts/create_tenant.py --slug <slug> ...`; login bằng Mã tổ chức
   tương ứng; career page tại `<slug>.hr.hpu.edu.vn`.
3. Rà lại `/security-review` cơ chế X-Org-Slug (ADR-006) ở bối cảnh nhiều tenant + cân nhắc
   rate-limit/log theo org.
