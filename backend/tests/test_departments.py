# Test cơ cấu tổ chức (departments): CRUD, chỉ admin sửa (HR chỉ xem), cây cha-con, isolation.

import pytest

from app.models.department import Department
from app.models.user import User
from tests.conftest import _make_user, auth_headers


@pytest.fixture
async def admin_org_a(db_session, org_a) -> User:
    u = _make_user(org_a, "admin.dep@hpu.edu.vn", org_role="admin")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _create(client, admin, **body):
    return await client.post("/api/v1/departments", json=body, headers=auth_headers(admin))


class TestDepartmentCRUD:
    async def test_admin_create_tree_and_list(self, async_client, admin_org_a):
        parent = await _create(async_client, admin_org_a, name="Phòng CNTT")
        assert parent.status_code == 201
        pid = parent.json()["data"]["id"]

        child = await _create(async_client, admin_org_a, name="Tổ Web", parent_id=pid)
        assert child.status_code == 201
        assert child.json()["data"]["parent_id"] == pid

        lst = await async_client.get("/api/v1/departments", headers=auth_headers(admin_org_a))
        assert lst.status_code == 200
        assert len(lst.json()["data"]) == 2

    async def test_hr_can_view_but_not_create(self, async_client, hr_manager_org_a):
        view = await async_client.get("/api/v1/departments", headers=auth_headers(hr_manager_org_a))
        assert view.status_code == 200  # xem = staff
        create = await _create(async_client, hr_manager_org_a, name="X")
        assert create.status_code == 403  # tạo = admin → HR bị chặn

    async def test_cannot_delete_with_children(self, async_client, admin_org_a):
        pid = (await _create(async_client, admin_org_a, name="Cha")).json()["data"]["id"]
        await _create(async_client, admin_org_a, name="Con", parent_id=pid)
        r = await async_client.delete(
            f"/api/v1/departments/{pid}", headers=auth_headers(admin_org_a)
        )
        assert r.status_code == 422

    async def test_self_parent_rejected(self, async_client, admin_org_a):
        did = (await _create(async_client, admin_org_a, name="P")).json()["data"]["id"]
        r = await async_client.put(
            f"/api/v1/departments/{did}",
            json={"parent_id": did},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 422


class TestDepartmentIsolation:
    async def test_cross_tenant_parent_404(self, async_client, db_session, admin_org_a, org_b):
        other = Department(organization_id=org_b.id, name="Org B Dept")
        db_session.add(other)
        await db_session.commit()
        await db_session.refresh(other)
        r = await _create(async_client, admin_org_a, name="X", parent_id=str(other.id))
        assert r.status_code == 404
