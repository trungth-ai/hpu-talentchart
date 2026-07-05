# DEPLOY.md — Runbook triển khai & Cutover go-live HPU (Sprint 8)

> Quy trình 7 bước theo `/deploy` + checklist HUONG-DAN §9. Người thực hiện: Trung.
> Server: HPU (Docker + caddy-docker-proxy, network `caddy-proxy` đã tạo bởi `~/hpu-dev/setup.sh`).

## 0. Điều kiện tiên quyết (làm 1 lần)

- [ ] DNS: `app.talentchart.hpu.edu.vn` + wildcard `*.talentchart.hpu.edu.vn` trỏ về server
- [ ] `CLOUDFLARE_API_TOKEN` có quyền DNS edit (wildcard SSL cho subdomain tenant)
- [ ] Google Cloud Console: tạo OAuth Client ID
  - Authorized JavaScript origins: `https://app.talentchart.hpu.edu.vn`, `https://hpu.talentchart.hpu.edu.vn`
  - (Dev: thêm `http://localhost:3000`)
- [ ] `cp .env.production.example .env.production` và điền đủ — **không giá trị nào rỗng**

## 1. Pre-flight check (trên máy dev / CI)

```bash
# Backend
cd backend && uv run ruff check . && uv run pytest --cov=app --cov-fail-under=70
# Frontend
cd frontend && npm ci && npm run typecheck && npm run build
# CI GitHub Actions phải xanh trên nhánh sẽ deploy
```

Checklist bắt buộc trước khi deploy production (HUONG-DAN §9):
- [ ] `/security-review --pr` sạch — đặc biệt Multi-tenant safety (RLS migration 0001-0003)
- [ ] `/review` đạt 7 tiêu chí
- [ ] `test_tenant_isolation.py` + toàn bộ suite pass (hiện tại: 460 tests)
- [ ] Coverage > 70%
- [ ] Nội dung 12 Archetype đã được Trung review (core IP — ADR-005)

## 2. Staging trước, production sau

```bash
# Trên server, lần đầu:
git clone https://github.com/trungth-ai/hpu-talentchart ~/hpu-dev/talentchart
cd ~/hpu-dev/talentchart

# Staging = chạy compose với domain staging hoặc test trên docker network nội bộ
docker compose --env-file .env.production up -d --build db redis
docker compose --env-file .env.production run --rm backend alembic upgrade head
```

## 3. Backup TRƯỚC migration (bắt buộc mỗi lần deploy)

```bash
docker compose exec db pg_dump -U talentchart -F c talentchart > backups/pre-deploy-$(date +%Y%m%d).dump
# Container backup tự chạy hằng ngày (scripts/backup-postgres.sh, giữ 14 ngày)
```

## 4. Migration + khởi động đầy đủ

```bash
docker compose --env-file .env.production up -d --build
docker compose exec backend alembic upgrade head
# Verify RLS đã bật (lớp bảo vệ số 3):
docker compose exec db psql -U talentchart -c \
  "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public';"
# → users, campaigns, candidates, job_posts, test_sessions đều rowsecurity = t
```

## 5. Khởi tạo dữ liệu HPU (cutover — chạy 1 lần duy nhất)

```bash
# 5.1 Tạo tenant HPU + tài khoản owner + bật Google Workspace domain
docker compose exec backend python scripts/create_tenant.py \
  --slug hpu --name "Trường Đại học Hải Phòng" \
  --email trungth@hpu.edu.vn --password "<mật-khẩu-mạnh>" \
  --google-domain hpu.edu.vn

# 5.2 Import 107 nhân sự từ file lương (đã có cơ sở đồng ý từ Fortune HR cũ)
# Copy file dữ liệu vào container trước (image không chứa file nhạy cảm):
docker cp "Luong T8.xlsx" talentchart-backend:/tmp/luong-t8.xlsx
docker cp contacts.csv talentchart-backend:/tmp/contacts.csv
docker compose exec backend python scripts/import_employees.py \
  --file /tmp/luong-t8.xlsx --org-slug hpu --with-epa-consent

# 5.3 Đối chiếu danh bạ → email thật + SĐT + địa chỉ (63/107 tự match)
docker compose exec backend python scripts/update_contacts.py \
  --csv /tmp/contacts.csv --org-slug hpu
# → Xử lý tay 5 người trùng tên + 38 người không có trong danh bạ (script in danh sách)

# 5.4 Bật Eastern Layer cho HPU (nếu muốn hiện Can Chi/Mệnh/Tam hợp)
# UPDATE organizations SET settings = settings || '{"eastern_layer_enabled": true}'
# WHERE slug = 'hpu';   -- hoặc chờ màn settings ở release sau
```

## 6. Smoke test production

```bash
curl -f https://app.talentchart.hpu.edu.vn/health
# Login (Postman/curl) → 200 + token:
curl -X POST https://app.talentchart.hpu.edu.vn/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"trungth@hpu.edu.vn","password":"..."}' \
  -H "Host: hpu.talentchart.hpu.edu.vn"
# Career page tenant: https://hpu.talentchart.hpu.edu.vn (public)
# Xác nhận CÔ LẬP TENANT: tạo org thử nghiệm thứ 2, xác nhận không thấy dữ liệu HPU
```

- [ ] Đăng nhập Google bằng tài khoản @hpu.edu.vn thật hoạt động
- [ ] Gửi 1 bài test DISC thật → làm bài → HR xem kết quả + archetype
- [ ] Case kiểm chứng EPA: Trần Hữu Nghị (1/1/1938) → Đinh Sửu

## 7. Rollback (khi có sự cố)

```bash
git reset --hard HEAD~1 && docker compose --env-file .env.production up -d --build
# Nếu migration đã chạy và cần lùi:
docker compose exec backend alembic downgrade -1
# Khôi phục dữ liệu từ backup bước 3:
docker compose exec -T db pg_restore -U talentchart -d talentchart --clean < backups/pre-deploy-*.dump
```

## Theo dõi sau go-live (HUONG-DAN §10)

- Log backend: `docker compose logs -f backend` (structlog JSON)
- Chi phí Anthropic API: narrative có cache — theo dõi usage console.anthropic.com
- Backup hằng ngày trong `./backups/` (container `talentchart-backup`, giữ 14 ngày)
- Mọi PR chạm query DB → `/security-review` trước merge
