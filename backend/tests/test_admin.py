# Test quản trị: đổi vai trò / khóa-mở user + cài đặt tổ chức.
# Nhấn mạnh CHỐT AN TOÀN: chỉ admin+, không tự sửa mình, không đụng quyền ngang/cao hơn,
# không cấp quyền >= mình, cross-tenant → 404.

import pytest

from app.models.user import User
from tests.conftest import _make_user, auth_headers


@pytest.fixture
async def admin_org_a(db_session, org_a) -> User:
    u = _make_user(org_a, "admin.a@hpu.edu.vn", org_role="admin")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def owner_org_a(db_session, org_a) -> User:
    u = _make_user(org_a, "owner.a@hpu.edu.vn", org_role="owner")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


class TestUserAdmin:
    async def test_admin_changes_lower_role(self, async_client, admin_org_a, member_org_a):
        r = await async_client.patch(
            f"/api/v1/users/{member_org_a.id}",
            json={"org_role": "recruiter"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 200
        assert r.json()["data"]["org_role"] == "recruiter"

    async def test_admin_deactivates_lower_user(
        self, async_client, db_session, admin_org_a, member_org_a
    ):
        r = await async_client.patch(
            f"/api/v1/users/{member_org_a.id}",
            json={"status": "inactive"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 200
        await db_session.refresh(member_org_a)
        assert member_org_a.status == "inactive"

    async def test_non_admin_forbidden(self, async_client, hr_manager_org_a, member_org_a):
        # hr_manager (dưới admin) KHÔNG được đổi vai trò người khác
        r = await async_client.patch(
            f"/api/v1/users/{member_org_a.id}",
            json={"org_role": "recruiter"},
            headers=auth_headers(hr_manager_org_a),
        )
        assert r.status_code == 403

    async def test_cannot_modify_self(self, async_client, admin_org_a):
        r = await async_client.patch(
            f"/api/v1/users/{admin_org_a.id}",
            json={"status": "inactive"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 422

    async def test_cannot_modify_equal_or_higher(self, async_client, admin_org_a, owner_org_a):
        # admin cố khóa owner (quyền cao hơn) → 403
        r = await async_client.patch(
            f"/api/v1/users/{owner_org_a.id}",
            json={"status": "inactive"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 403

    async def test_cannot_grant_role_ge_own(self, async_client, admin_org_a, member_org_a):
        # admin cấp vai trò admin (ngang mình) cho member → 403
        r = await async_client.patch(
            f"/api/v1/users/{member_org_a.id}",
            json={"org_role": "admin"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 403

    async def test_cross_tenant_404(self, async_client, admin_org_a, hr_manager_org_b):
        r = await async_client.patch(
            f"/api/v1/users/{hr_manager_org_b.id}",
            json={"org_role": "member"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 404


class TestOrganizationSettings:
    async def test_get_organization(self, async_client, hr_manager_org_a):
        r = await async_client.get("/api/v1/organization", headers=auth_headers(hr_manager_org_a))
        assert r.status_code == 200
        assert "settings" in r.json()["data"]

    async def test_admin_updates_settings(self, async_client, admin_org_a):
        r = await async_client.put(
            "/api/v1/organization/settings",
            json={"eastern_layer_enabled": True, "google_workspace_domain": "hpu.edu.vn"},
            headers=auth_headers(admin_org_a),
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["settings"]["eastern_layer_enabled"] is True
        assert data["settings"]["google_workspace_domain"] == "hpu.edu.vn"

    async def test_non_admin_cannot_update_settings(self, async_client, hr_manager_org_a):
        r = await async_client.put(
            "/api/v1/organization/settings",
            json={"eastern_layer_enabled": True},
            headers=auth_headers(hr_manager_org_a),
        )
        assert r.status_code == 403
