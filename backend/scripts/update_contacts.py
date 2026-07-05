# Đối chiếu danh bạ Google Contacts (export CSV) với danh sách nhân sự đã import
# → cập nhật email thật @hpu.edu.vn (thay placeholder), số điện thoại, địa chỉ.
#
# Cách match: tên trong danh bạ KHÔNG DẤU (VD "Bui Xuan Hien", có prefix đơn vị
# "(B. Baove) ..."), tên nhân sự CÓ DẤU (VD "Bùi Xuân Hiển") → chuẩn hóa cả hai
# về dạng không dấu + lowercase rồi so khớp. Chỉ cập nhật khi match DUY NHẤT
# ở cả hai phía; trường hợp trùng tên → báo cáo để xử lý tay.
#
# Chạy (từ backend/, cần env DATABASE_URL + JWT_SECRET):
#   python scripts/update_contacts.py --csv "path/to/contacts.csv" --org-slug hpu [--dry-run]

import argparse
import asyncio
import csv
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.tenant_context import reset_current_org_id, set_current_org_id  # noqa: E402
from app.database import async_session_factory, set_rls_guc  # noqa: E402
from app.models import Candidate, Organization  # noqa: E402


def normalize_name(name: str) -> str:
    """'(B. Baove) Bùi Xuân Hiển ' → 'bui xuan hien' (bỏ prefix ngoặc, bỏ dấu)."""
    name = re.sub(r"\([^)]*\)", " ", name)  # bỏ prefix đơn vị trong ngoặc
    name = name.replace("đ", "d").replace("Đ", "D")
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", name).strip().lower()


def parse_contacts(csv_path: str) -> dict[str, list[dict]]:
    """Đọc CSV Google Contacts → {tên chuẩn hóa: [contact...]} (chỉ contact có email hpu)."""
    contacts: dict[str, list[dict]] = defaultdict(list)
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Lấy email hpu.edu.vn đầu tiên trong 3 cột email
            email = None
            for i in (1, 2, 3):
                value = (row.get(f"E-mail {i} - Value") or "").strip().lower()
                # 1 ô có thể chứa nhiều email phân cách ' ::: '
                for candidate_email in value.split(":::"):
                    candidate_email = candidate_email.strip()
                    if candidate_email.endswith("@hpu.edu.vn"):
                        email = candidate_email
                        break
                if email:
                    break
            if not email:
                continue

            name = normalize_name(row.get("First Name") or "")
            if not name:
                continue

            # SĐT đầu tiên (cắt phần ' ::: ' nếu nhiều số)
            phone = (row.get("Phone 1 - Value") or "").split(":::")[0].strip() or None
            address = (row.get("Address 1 - Formatted") or "").strip() or None

            contacts[name].append({"email": email, "phone": phone, "address": address})
    return contacts


async def update_contacts(csv_path: str, org_slug: str, dry_run: bool) -> None:
    contacts = parse_contacts(csv_path)
    total_contacts = sum(len(v) for v in contacts.values())
    print(f"[INFO] Danh ba co {total_contacts} lien he @hpu.edu.vn ({len(contacts)} ten)")

    async with async_session_factory() as session:
        org = (
            await session.execute(select(Organization).where(Organization.slug == org_slug))
        ).scalar_one_or_none()
        if org is None:
            raise SystemExit(f"[LOI] Khong tim thay organization slug '{org_slug}'")

        token = set_current_org_id(org.id)
        try:
            await set_rls_guc(session)
            employees = (
                (
                    await session.execute(
                        select(Candidate)
                        .where(Candidate.organization_id == org.id)
                        .where(Candidate.candidate_type == "employee")
                        .where(Candidate.status == "active")
                    )
                )
                .scalars()
                .all()
            )
            print(f"[INFO] Co {len(employees)} nhan su trong he thong")

            # Gom nhân sự theo tên chuẩn hóa để phát hiện trùng tên
            emp_by_name: dict[str, list[Candidate]] = defaultdict(list)
            for e in employees:
                emp_by_name[normalize_name(e.full_name)].append(e)

            updated, ambiguous, unmatched = 0, [], []
            for name, emps in emp_by_name.items():
                matches = contacts.get(name, [])
                if not matches:
                    unmatched.extend(e.full_name for e in emps)
                    continue
                if len(emps) > 1 or len(matches) > 1:
                    ambiguous.append(
                        f"{emps[0].full_name} (x{len(emps)} NV / x{len(matches)} contact)"
                    )
                    continue

                emp, contact = emps[0], matches[0]
                changes = []
                # Email: chỉ thay khi đang là placeholder import
                if emp.email.endswith("@import.hpu.edu.vn") and contact["email"]:
                    changes.append(f"email {emp.email} -> {contact['email']}")
                    emp.email = contact["email"]
                if contact["phone"] and not emp.phone:
                    changes.append(f"phone -> {contact['phone']}")
                    emp.phone = contact["phone"][:20]
                if contact["address"] and not emp.address:
                    changes.append("address -> co")
                    emp.address = contact["address"][:255]

                if changes:
                    updated += 1
                    if dry_run:
                        print(f"  [DRY] {emp.full_name}: {'; '.join(changes)}")

            if dry_run:
                await session.rollback()
            else:
                await session.commit()
        finally:
            reset_current_org_id(token)

    print(f"[OK] Cap nhat {updated} nhan su" + (" (DRY-RUN, chua ghi DB)" if dry_run else ""))
    if ambiguous:
        print(f"[CHU Y] {len(ambiguous)} truong hop trung ten can xu ly tay:")
        for a in ambiguous:
            print("  -", a)
    if unmatched:
        print(f"[CHU Y] {len(unmatched)} nhan su KHONG tim thay trong danh ba:")
        for u in unmatched[:15]:
            print("  -", u)
        if len(unmatched) > 15:
            print(f"  ... va {len(unmatched) - 15} nguoi nua")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Doi chieu danh ba, cap nhat email/phone/dia chi")
    parser.add_argument("--csv", required=True, help="Duong dan file contacts.csv (Google export)")
    parser.add_argument("--org-slug", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    asyncio.run(update_contacts(args.csv, args.org_slug, args.dry_run))
