# HANDOFF — TalentChart (cập nhật 2026-07-09)

Tài liệu bàn giao: tóm tắt TOÀN BỘ các phần đã hoàn thành trong đợt làm việc này, cách
triển khai, và các điểm còn hạn chế. Repo: `github.com/trungth-ai/hpu-talentchart`
(nhánh `main`). Server: `ubuntu210:~/trungth/hpu-talentchart`, domain `hr.hpu.edu.vn`.

---

## 1. Sửa deploy & kiến trúc domain (ADR-006)

- **Lỗi proxy `/api → localhost:8003`**: Next.js đóng băng rewrites lúc BUILD → phải
  truyền `BACKEND_INTERNAL_URL` là build ARG (frontend/Dockerfile). Rebuild frontend
  là hết.
- **Bug môi trường**: `docker-compose.yml` set `ENV=production` nhưng `config.py` đọc
  `APP_ENV` → prod chạy nhầm `development`. Đã sửa: `APP_ENV=${APP_ENV:-production}`.
- **ADR-006**: domain phẳng `hr.hpu.edu.vn` → login staff resolve tổ chức qua header
  **`X-Org-Slug`** ("Mã tổ chức"), honor ở mọi môi trường (chỉ là fallback sau
  JWT + subdomain). Career page: `hpu.hr.hpu.edu.vn`. Caddy hệ thống → `localhost:3300`.
- `docs/DEPLOY.md` đã viết lại theo mô hình này.
- **Lưu ý vận hành**: server chỉ nên `git pull`; đừng commit/gỡ guard `:?` trong compose.

## 2. CRUD nhân sự (frontend)

Backend đã có sẵn POST/PUT/DELETE. Bổ sung UI: nút **Thêm** (trang list), **Sửa/Xóa**
(trang chi tiết). Xóa = soft-delete (`status=inactive`). Modal dùng chung
`components/features/candidate-form-modal.tsx`. Có trường **Giới tính** (nam/nữ) —
dùng cho so sánh tương hợp.

## 3. EPA — Tính cách đặc trưng (2.4)

Trang chi tiết ứng viên (cần `epa_consent` + `birth_date`) hiển thị:
- **Con giáp** (theo tuổi) + **Cung hoàng đạo** (theo ngày sinh): tính cách, điểm
  mạnh/yếu, nghề phù hợp, màu sắc. Nguồn: `app/data/zodiac_animals.py`,
  `app/data/horoscope.py` (chắt lọc từ tài liệu Trung cung cấp).
- Nút **"Xem thêm — toàn diện"**: modal hiện NGUYÊN VĂN đầy đủ 3 sách (con giáp +
  "12 Chòm Sao" + "Tử Vi Tây"), lưu ở bảng DB `astrology_reference` (migration 0006),
  nạp bằng `scripts/seed_astrology.py` (đọc `app/data/astrology_full.json`).

## 4. Nhịp sinh học — Biorhythm (2.3)

`app/services/epa/biorhythm.py` (thể chất 23 / cảm xúc 28 / trí tuệ 33 ngày) →
endpoint `/epa/candidates/{id}/biorhythm` → biểu đồ SVG (`biorhythm-chart.tsx`).

## 5. Vận trình ngày/tháng (2.1/2.2)

- `app/services/epa/fortune.py`: Can Chi tính offline + **Claude (`claude-sonnet-5`)
  diễn giải** vận trình ngày + tháng (fallback template nếu thiếu `ANTHROPIC_API_KEY`).
  Vận trình tháng có nạp "chỉ nam mỗi tháng" theo sách (kind='month').
- **Cào lichngaytot** (best-effort, bấm nút mới chạy) — endpoint
  `/epa/candidates/{id}/lichngaytot`, lấy 3 nguồn:
  - Ngày tốt/xấu, sao, giờ hoàng đạo: `/xem-ngay-tot-xau-DD-MM-YYYY`
  - Tử vi ngày theo tuổi: crawl `/tu-vi.html` → bài `tu-vi-hang-ngay-D-M-YYYY-...`
  - Tử vi ngày theo cung: `/cung-hoang-dao/{slug}.html`

## 6. So sánh tương hợp (EPA) — có xét giới tính

- **Quan hệ tuổi truyền thống** (`compatibility.relationship`): tam hợp / lục hợp /
  lục xung / lục hại + ngũ hành tương sinh/khắc — TRUNG TÍNH giới, hiện cho MỌI cặp.
- `compatibility_score()` GIỮ NGUYÊN (parity Fortune HR: Tam hợp 75, Xung 20).
- **Mô tả hôn nhân** (từ ma trận gendered trong sách con giáp) CHỈ hiện khi cặp
  **nam–nữ**; cùng giới / thiếu giới tính → ghi chú trung tính (không luận vợ chồng).

---

## Triển khai (server)

```bash
cd ~/trungth/hpu-talentchart
# .env.production cần: APP_DOMAIN=hr.hpu.edu.vn, FRONTEND_PORT=3300, APP_ENV=production,
#   JWT_SECRET, DB_PASSWORD, REDIS_PASSWORD, MINIO_ACCESS_KEY/SECRET_KEY, ANTHROPIC_API_KEY
git pull origin main
docker compose --env-file .env.production build --no-cache backend frontend
docker compose --env-file .env.production up -d
docker compose --env-file .env.production exec backend alembic upgrade head          # migration 0001..0007
docker compose --env-file .env.production exec backend python scripts/seed_astrology.py  # nạp nội dung tử vi (idempotent)
```

Cutover dữ liệu HPU (1 lần): `create_tenant.py` (org hpu + owner), `import_employees.py`,
`update_contacts.py` — xem `docs/DEPLOY.md` bước 5.

## Hạn chế đã biết (do OCR/nguồn không đồng đều)

- **Cào lichngaytot**: best-effort, phụ thuộc HTML trang ngoài; phần "theo cung" đôi khi
  bị site chặn (bỏ qua phần đó, không lỗi toàn cục).
- **Mô tả hôn nhân theo sách** (so sánh tương hợp): 9/12 tuổi có, một số chỉ có 1 khối
  giới (Dần/Tỵ/Ngọ không có trong sách). **Quan hệ tuổi truyền thống luôn phủ đủ 12×12.**
- **Chỉ nam tháng**: 9/12 cung (Song Tử/Bảo Bình/Ma Kết thiếu do định dạng OCR).
- Nội dung tử vi cần Trung review (core IP) trước go-live.

## Tài liệu nguồn & script (không commit dữ liệu thô)

- Tài liệu: `12_con_giap_theo_lich_van_nien.md`, `12 Chòm Sao Và Đời Người...pdf`,
  `Tu-Vi-Tay.pdf` (ở Downloads máy Trung — KHÔNG trong repo, đã gitignore xlsx/csv).
- Nội dung đã cấu trúc hóa: `backend/app/data/astrology_full.json` (commit).

## Kiểm thử

`backend/.venv/Scripts/python -m pytest` → **485 pass**. Frontend: `npm run build` xanh.
