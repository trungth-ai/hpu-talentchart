# ★ CRITICAL — Test cô lập tenant (PLAN.md Story 2, rules/tenant-isolation.md quy tắc 7)
# 2 organization không bao giờ thấy dữ liệu của nhau. Cross-tenant → 404, KHÔNG 403.

import pytest
from sqlalchemy import select

from app.core.tenant_context import reset_current_org_id, set_current_org_id
from app.models import User
from tests.conftest import auth_headers


class TestCrossTenantAPI:
    """Lớp 1+2: cô lập qua API — user org A không list/get được user org B."""

    async def test_get_other_org_user_returns_404_not_403(
        self, async_client, hr_manager_org_a, hr_manager_org_b
    ):
        # User org A truy cập user org B theo id → PHẢI 404 (không leak existence)
        response = await async_client.get(
            f"/api/v1/users/{hr_manager_org_b.id}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 404
        assert response.status_code != 403
        body = response.json()
        assert body["status"] == "error"
        assert body["code"] == "NOT_FOUND"

    async def test_get_own_org_user_returns_200(
        self, async_client, hr_manager_org_a, member_org_a
    ):
        response = await async_client.get(
            f"/api/v1/users/{member_org_a.id}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        assert response.json()["data"]["email"] == member_org_a.email

    async def test_list_users_only_shows_own_org(
        self, async_client, hr_manager_org_a, member_org_a, hr_manager_org_b
    ):
        response = await async_client.get(
            "/api/v1/users", headers=auth_headers(hr_manager_org_a)
        )
        assert response.status_code == 200
        body = response.json()
        emails = {u["email"] for u in body["data"]}
        # Chỉ thấy 2 user của org A, tuyệt đối không thấy user org B
        assert emails == {hr_manager_org_a.email, member_org_a.email}
        assert hr_manager_org_b.email not in emails
        assert body["meta"]["total"] == 2

    async def test_response_never_contains_organization_id(
        self, async_client, hr_manager_org_a
    ):
        # Rule số 6: response KHÔNG include organization_id (tránh leak)
        response = await async_client.get(
            "/api/v1/users", headers=auth_headers(hr_manager_org_a)
        )
        for user in response.json()["data"]:
            assert "organization_id" not in user

    async def test_jwt_takes_priority_over_dev_header(
        self, async_client, hr_manager_org_a, hr_manager_org_b, org_b
    ):
        # Token org A + header X-Org-Slug trỏ org B → JWT thắng, vẫn chỉ thấy org A
        headers = {**auth_headers(hr_manager_org_a), "X-Org-Slug": org_b.slug}
        response = await async_client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200
        emails = {u["email"] for u in response.json()["data"]}
        assert hr_manager_org_b.email not in emails


class TestORMAutoFilter:
    """Lớp 2: SQLAlchemy event listener tự inject filter organization_id."""

    async def test_select_auto_filtered_by_tenant_context(
        self, db_session, hr_manager_org_a, hr_manager_org_b, org_a
    ):
        token = set_current_org_id(org_a.id)
        try:
            result = await db_session.execute(select(User))
            users = result.scalars().all()
            assert len(users) == 1
            assert users[0].organization_id == org_a.id
        finally:
            reset_current_org_id(token)

    async def test_select_without_context_not_filtered(
        self, db_session, hr_manager_org_a, hr_manager_org_b
    ):
        # Không có tenant context (script hệ thống) → thấy tất cả
        # (trên production, RLS PostgreSQL sẽ chặn thêm 1 lớp nữa)
        result = await db_session.execute(select(User))
        assert len(result.scalars().all()) == 2

    async def test_flush_guard_blocks_wrong_tenant_write(
        self, db_session, org_a, org_b
    ):
        # Đang ở context org A mà ghi user mang organization_id của org B → chặn ngay
        token = set_current_org_id(org_a.id)
        try:
            intruder = User(
                organization_id=org_b.id,
                email="hacker@evil.com",
                username="hacker",
                full_name="Kẻ Xâm Nhập",
                hashed_password="x",
            )
            db_session.add(intruder)
            with pytest.raises(PermissionError):
                await db_session.flush()
        finally:
            reset_current_org_id(token)
        await db_session.rollback()

    async def test_new_object_auto_gets_context_org_id(self, db_session, org_a):
        # Object mới không set organization_id → tự lấy từ context (không bao giờ từ client)
        token = set_current_org_id(org_a.id)
        try:
            user = User(
                email="auto@hpu.edu.vn",
                username="auto",
                full_name="Tự Gán Org",
                hashed_password="x",
            )
            db_session.add(user)
            await db_session.flush()
            assert user.organization_id == org_a.id
        finally:
            reset_current_org_id(token)
        await db_session.rollback()


class TestLoginScoping:
    """Login scoped theo tổ chức — cùng email ở 2 org là 2 tài khoản độc lập."""

    async def test_same_email_two_orgs_login_separately(
        self, async_client, db_session, org_a, org_b
    ):
        from tests.conftest import _make_user

        db_session.add(_make_user(org_a, "chung@mail.com"))
        db_session.add(_make_user(org_b, "chung@mail.com"))
        await db_session.commit()

        # Login qua org A (dev header) → nhận về user thuộc org A
        resp_a = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "chung@mail.com", "password": "MatKhau@123"},
            headers={"X-Org-Slug": "hpu"},
        )
        resp_b = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "chung@mail.com", "password": "MatKhau@123"},
            headers={"X-Org-Slug": "alpha"},
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        # 2 org trả về 2 user id khác nhau dù email giống nhau
        assert resp_a.json()["data"]["user"]["id"] != resp_b.json()["data"]["user"]["id"]

    async def test_login_via_subdomain(self, async_client, org_a, hr_manager_org_a):
        # Resolve tenant qua subdomain: hpu.talentchart.hpu.edu.vn
        response = await async_client.post(
            "http://hpu.talentchart.hpu.edu.vn/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "MatKhau@123"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"
