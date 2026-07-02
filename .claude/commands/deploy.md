# /deploy — Build + deploy Docker

## Khi nào dùng

User chạy `/deploy` để build Docker image và deploy lên server.

## Việc cần làm

### Step 1 — Pre-flight checks

Kiểm tra:
- [ ] `docker` và `docker compose` cài đặt
- [ ] `.env.production` tồn tại và có đủ variables required
- [ ] Network `caddy-proxy` đã tồn tại
- [ ] Health endpoint trong code: `GET /health`
- [ ] Tất cả tests pass: `docker compose exec backend uv run pytest`
- [ ] Lint pass: `docker compose exec backend uv run ruff check .`
- [ ] (SaaS) mypy pass: `docker compose exec backend uv run mypy app/`
- [ ] Migration ready (SaaS): `alembic upgrade head` test

### Step 2 — Build images

```bash
docker compose --env-file .env.production build
```

Verify:
- Image size hợp lý (<500MB cho FastAPI, <300MB cho Next.js standalone)
- Build không có warning critical

### Step 3 — Test locally trước

```bash
docker compose --env-file .env.production up -d
sleep 10
curl -f http://localhost:8003/health || (echo "Health check failed" && exit 1)
docker compose logs backend | tail -20
```

### Step 4 — Push code lên Git (nếu user OK)

```bash
git status
git add .
git commit -m "feat: deploy v{version}"
git push origin main
```

### Step 5 — Deploy lên server

```bash
ssh root@hpu-server "cd /root/trungth/{project} && \
    git pull origin main && \
    docker compose --env-file .env.production up -d --build && \
    docker compose ps"
```

### Step 6 — Verify production

```bash
# Verify health
curl -f https://{domain}/health

# Verify tests endpoint
curl -f https://{domain}/api/v1/health

# Check logs có error không
ssh root@hpu-server "cd /root/trungth/{project} && docker compose logs --tail=50 backend"
```

### Step 7 — Notify

Gửi notification (nếu config Telegram bot):
```
✅ Deploy {project} thành công
- Version: v{version}
- Time: {datetime}
- URL: https://{domain}
```

## Output cho user

```
✅ Deploy hoàn thành

🏗️  Build:
- Backend image: {size}
- Frontend image: {size} (SaaS only)

🚀 Deployed:
- Production URL: https://{domain}
- Health check: ✅ OK
- Tests: ✅ {N}/{N} pass
- Migration: ✅ Up to date (SaaS)

📊 Status:
- Containers running: {N}/{N}
- Last deploy: {datetime}
- Git commit: {hash}

📝 Bước tiếp theo:
- Monitor logs trong 10 phút đầu: docker compose logs -f
- Smoke test các flow chính
- Cập nhật CHANGELOG.md
```

## Rollback

Nếu deploy fail:
```bash
ssh root@hpu-server "cd /root/trungth/{project} && \
    git reset --hard HEAD~1 && \
    docker compose --env-file .env.production up -d --build"
```

## Gotchas

- ⚠️ KHÔNG deploy thẳng nếu tests fail
- ⚠️ Migration phải test trên staging trước
- ⚠️ Backup DB trước khi deploy có schema change (SaaS)
- ⚠️ Caddy auto-reload khi container start với labels mới
- ⚠️ KHÔNG deploy lúc giờ làm việc nếu có downtime risk
