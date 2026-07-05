# Test auth — login/refresh/me + rate limit (PLAN.md Story 1)

from tests.conftest import auth_headers


class TestLogin:
    async def test_login_success_returns_envelope_and_tokens(
        self, async_client, org_a, hr_manager_org_a
    ):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "MatKhau@123"},
            headers={"X-Org-Slug": org_a.slug},
        )
        assert response.status_code == 200
        body = response.json()
        # Envelope chuẩn (rules/api-response.md)
        assert body["status"] == "success"
        assert "message" in body
        data = body["data"]
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == hr_manager_org_a.email
        # Response không leak organization_id và hashed_password
        assert "organization_id" not in data["user"]
        assert "hashed_password" not in data["user"]

    async def test_access_token_contains_required_claims(
        self, async_client, org_a, hr_manager_org_a
    ):
        # Acceptance criteria: JWT chứa user_id, organization_id, org_role, system_role
        from app.core.security import decode_token

        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "MatKhau@123"},
            headers={"X-Org-Slug": org_a.slug},
        )
        payload = decode_token(response.json()["data"]["access_token"])
        assert payload["sub"] == str(hr_manager_org_a.id)
        assert payload["organization_id"] == str(org_a.id)
        assert payload["org_role"] == "hr_manager"
        assert payload["system_role"] == "user"

    async def test_login_wrong_password_returns_401(
        self, async_client, org_a, hr_manager_org_a
    ):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "SaiMatKhau"},
            headers={"X-Org-Slug": org_a.slug},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "UNAUTHORIZED"

    async def test_login_unknown_email_same_message_as_wrong_password(
        self, async_client, org_a, hr_manager_org_a
    ):
        # Không leak email có tồn tại hay không — cùng 1 thông báo lỗi
        resp_unknown = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "khongtontai@x.vn", "password": "MatKhau@123"},
            headers={"X-Org-Slug": org_a.slug},
        )
        resp_wrong = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "SaiMatKhau"},
            headers={"X-Org-Slug": org_a.slug},
        )
        assert resp_unknown.status_code == resp_wrong.status_code == 401
        assert resp_unknown.json()["message"] == resp_wrong.json()["message"]

    async def test_login_without_org_context_rejected(
        self, async_client, hr_manager_org_a
    ):
        # Không subdomain, không dev header → không xác định được tổ chức
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "MatKhau@123"},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "BUSINESS_RULE_ERROR"

    async def test_login_invalid_email_format_returns_422(self, async_client, org_a):
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "khong-phai-email", "password": "x"},
            headers={"X-Org-Slug": org_a.slug},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert any(e["field"] == "email" for e in body["errors"])

    async def test_login_rate_limited_after_5_attempts(
        self, async_client, org_a, hr_manager_org_a
    ):
        # Acceptance criteria: sai mật khẩu 5 lần/phút/IP → 429
        for _ in range(5):
            await async_client.post(
                "/api/v1/auth/login",
                json={"email": hr_manager_org_a.email, "password": "SaiMatKhau"},
                headers={"X-Org-Slug": org_a.slug},
            )
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "SaiMatKhau"},
            headers={"X-Org-Slug": org_a.slug},
        )
        assert response.status_code == 429
        assert response.json()["code"] == "RATE_LIMIT"


class TestRefresh:
    async def test_refresh_returns_new_token_pair(
        self, async_client, org_a, hr_manager_org_a
    ):
        login = await async_client.post(
            "/api/v1/auth/login",
            json={"email": hr_manager_org_a.email, "password": "MatKhau@123"},
            headers={"X-Org-Slug": org_a.slug},
        )
        refresh_token = login.json()["data"]["refresh_token"]

        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["access_token"]
        assert data["refresh_token"]

    async def test_refresh_rejects_access_token(
        self, async_client, hr_manager_org_a
    ):
        # Đưa access token vào chỗ refresh token → 401 (sai loại token)
        from app.core.security import create_access_token

        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": create_access_token(hr_manager_org_a)},
        )
        assert response.status_code == 401

    async def test_refresh_rejects_garbage_token(self, async_client):
        response = await async_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "token-rac"}
        )
        assert response.status_code == 401


class TestMe:
    async def test_me_returns_current_user(self, async_client, hr_manager_org_a):
        response = await async_client.get(
            "/api/v1/auth/me", headers=auth_headers(hr_manager_org_a)
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == hr_manager_org_a.email
        assert "organization_id" not in data

    async def test_me_without_token_returns_401(self, async_client):
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == 401

    async def test_me_with_invalid_token_returns_401(self, async_client):
        response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer token-gia"}
        )
        assert response.status_code == 401


class TestPermissions:
    async def test_member_cannot_list_users_403(self, async_client, member_org_a):
        # Thiếu quyền hệ thống (role thấp) → 403 FORBIDDEN (khác cross-tenant = 404)
        response = await async_client.get(
            "/api/v1/users", headers=auth_headers(member_org_a)
        )
        assert response.status_code == 403
        assert response.json()["code"] == "FORBIDDEN"


class TestHealth:
    async def test_health_no_auth_required(self, async_client):
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
