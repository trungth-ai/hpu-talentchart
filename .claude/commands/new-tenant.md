# /new-tenant — Tạo organization (tenant) mới (chỉ SaaS)

Áp dụng cho: SaaS multi-tenant projects (TalentChart...)

## Khi nào dùng

User chạy `/new-tenant {slug}` để tạo organization mới trong DB SaaS.

Ví dụ:
- `/new-tenant hpu` → tạo org HPU
- `/new-tenant truong-x` → tạo org Trường X

## Việc cần làm

1. **Verify project là SaaS** (có file `src/models/organization.py`). Nếu là internal tool, dừng lại.

2. **Hỏi thêm thông tin** từ user:
   - Tên đầy đủ của tổ chức (ví dụ: "Trường ĐH Quản lý và Công nghệ Hải Phòng")
   - Tên ngắn (ví dụ: "HPU")
   - Loại: university / college / agency / company
   - Tier: starter / standard / premier
   - Email liên hệ
   - Subdomain mong muốn (default = slug)

3. **Tạo migration Alembic** thêm row vào bảng `organizations`:
   ```python
   def upgrade():
       op.execute(f"""
           INSERT INTO organizations (id, slug, name, name_short, type, tier,
                                      contact_email, subdomain, is_active)
           VALUES ('{uuid}', '{slug}', '{name}', '{short}', '{type}', '{tier}',
                   '{email}', '{subdomain}', TRUE)
       """)

   def downgrade():
       op.execute(f"DELETE FROM organizations WHERE slug = '{slug}'")
   ```

4. **Tạo super admin user đầu tiên** cho tenant:
   - Username, email, password mặc định `Hpu@2026` (must change first login)
   - Org role: `owner`

5. **Verify subdomain config**:
   - Check Caddy đã có wildcard cho `*.talentchart.hpu.edu.vn`
   - Nếu user dùng custom domain, hỏi DNS đã trỏ đúng chưa

6. **Output cho user**:
   ```
   ✅ Tạo organization {slug} thành công

   📋 Thông tin:
   - URL admin:    https://app.talentchart.hpu.edu.vn (login với credentials bên dưới)
   - URL public:   https://{slug}.talentchart.hpu.edu.vn (career page)
   - Tenant ID:    {uuid}

   🔑 Tài khoản admin đầu tiên:
   - Email:        {email}
   - Password:     Hpu@2026 (BUỘC PHẢI ĐỔI khi login lần đầu)

   📝 Bước tiếp theo:
   1. Chạy migration: docker compose exec backend uv run alembic upgrade head
   2. Login vào admin app, đổi password
   3. Mời thêm user vào org qua Settings → Users
   4. Cấu hình branding, logo, custom domain (Phase 2)
   ```

## Gotchas

- ⚠️ Slug phải unique và URL-safe (chỉ a-z, 0-9, dấu gạch ngang)
- ⚠️ KHÔNG hard-code data — luôn qua migration để có audit trail
- ⚠️ Password mặc định phải force change (must_change_password = TRUE)
- ⚠️ Trial period: nếu tier = "starter", set trial_ends_at = now() + 30 days
- ⚠️ Ghi audit log entry "ORGANIZATION_CREATED"
