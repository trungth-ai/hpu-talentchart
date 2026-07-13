# TIEN ICH TEST: dua toan bo NHAN SU (candidate_type=employee) ve buoc RECEIVED (Tiep nhan)
# de test luong DISC (gui/lam bai test). Chay THU CONG tren server:
#   docker compose exec backend python scripts/reset_disc_test.py          # reset ve RECEIVED
#   docker compose exec backend python scripts/reset_disc_test.py --hire   # tra lai HIRED
#
# LUU Y: thao tac nay DOI trang thai pipeline cua nhan su (dang HIRED). Chi dung de TEST,
# KHONG chay khi deploy. Xu ly theo TUNG to chuc + set RLS GUC de qua duoc Row Level Security
# tren PostgreSQL (script chay ngoai request nen phai tu set tenant context + GUC).

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.tenant_context import reset_current_org_id, set_current_org_id  # noqa: E402
from app.database import async_session_factory, set_rls_guc  # noqa: E402
from app.models.candidate import Candidate  # noqa: E402
from app.models.organization import Organization  # noqa: E402


async def run(target_stage: str) -> None:
    # Bang organizations la root (khong RLS) -> lay duoc danh sach to chuc ma khong can context
    async with async_session_factory() as session:
        orgs = (await session.execute(select(Organization.id, Organization.slug))).all()

    total = 0
    for org_id, slug in orgs:
        token = set_current_org_id(org_id)
        try:
            async with async_session_factory() as session:
                await set_rls_guc(session)  # set app.current_org_id cho RLS (PostgreSQL)
                rows = await session.execute(
                    select(Candidate).where(Candidate.candidate_type == "employee")
                )
                count = 0
                for candidate in rows.scalars().all():
                    candidate.pipeline_stage = target_stage
                    count += 1
                await session.commit()
                total += count
                print(f"  - {slug}: {count} nhan su -> {target_stage}")
        finally:
            reset_current_org_id(token)

    print(f"[OK] Da doi {total} nhan su sang trang thai {target_stage}.")


if __name__ == "__main__":
    stage = "HIRED" if "--hire" in sys.argv else "RECEIVED"
    asyncio.run(run(stage))
