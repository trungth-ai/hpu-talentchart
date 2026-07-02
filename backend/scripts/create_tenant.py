# Script tạo organization (tenant) mới + user owner đầu tiên
# Dùng cho acceptance testing Sprint 1 và slash-command /new-tenant
#
# Chạy (trong container hoặc venv, từ thư mục backend/):
#   uv run python scripts/create_tenant.py --slug hpu --name "Trường ĐH Hải Phòng" \
#       --email admin@hpu.edu.vn --password "MatKhauManh@2026"

import argparse
import asyncio
import sys
from pathlib import Path

# Cho phép import app/ khi chạy trực tiếp
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.core.tenant_context import reset_current_org_id, set_current_org_id  # noqa: E402
from app.database import async_session_factory, set_rls_guc  # noqa: E402
from app.models import Organization, User  # noqa: E402


async def create_tenant(slug: str, name: str, email: str, password: str) -> None:
    async with async_session_factory() as session:
        # Kiểm tra slug trùng
        existing = await session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if existing.scalar_one_or_none():
            print(f"❌ Organization slug '{slug}' đã tồn tại")
            return

        org = Organization(name=name, slug=slug)
        session.add(org)
        await session.flush()  # lấy org.id trước khi tạo user

        # Set tenant context + RLS GUC để INSERT user qua được policy
        token = set_current_org_id(org.id)
        try:
            await set_rls_guc(session)
            owner = User(
                organization_id=org.id,
                email=email.lower(),
                username=email.split("@")[0].lower(),
                full_name="Quản trị viên",
                hashed_password=hash_password(password),
                org_role="owner",
            )
            session.add(owner)
            await session.commit()
        finally:
            reset_current_org_id(token)

        print(f"✅ Đã tạo organization '{name}' (slug: {slug})")
        print(f"   Owner: {email} — đăng nhập tại https://{slug}.talentchart.hpu.edu.vn")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo tenant mới cho TalentChart")
    parser.add_argument("--slug", required=True, help="Slug subdomain (VD: hpu)")
    parser.add_argument("--name", required=True, help="Tên tổ chức")
    parser.add_argument("--email", required=True, help="Email user owner")
    parser.add_argument("--password", required=True, help="Mật khẩu user owner")
    args = parser.parse_args()

    asyncio.run(create_tenant(args.slug, args.name, args.email, args.password))
