# Test Google OAuth (ADR-004) — verify_google_id_token được mock, không gọi Google thật

import pytest
from sqlalchemy import select

from app.models.candidate import Candidate
from app.models.organization import Organization
from app.models.user import User
from app.services import google_auth


@pytest.fixture
async def org_google(db_session) -> Organization:
    """Org đã bật Google Workspace domain hpu.edu.vn."""
    org = Organization(
        name="Trường ĐH Hải Phòng",
        slug="hpugg",
        settings={
            "eastern_layer_enabled": False,
            "google_workspace_domain": "hpu.edu.vn",
            "google_auto_provision": True,
        },
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


def _mock_google(monkeypatch, email: str, name: str = "Người Dùng Google"):
    """Giả lập Google verify thành công với email cho trước."""

    async def fake_verify(id_token: str) -> dict:
        return {"email": email, "email_verified": "true", "name": name, "sub": "gg-123"}

    monkeypatch.setattr(google_auth, "verify_google_id_token", fake_verify)


class TestStaffGoogleLogin:
    async def test_hpu_domain_auto_provision_and_login(
        self, async_client, db_session, org_google, monkeypatch
    ):
        _mock_google(monkeypatch, "giangvien@hpu.edu.vn", "Giảng Viên A")

        response = await async_client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
            headers={"X-Org-Slug": org_google.slug},
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["access_token"]
        assert data["user"]["email"] == "giangvien@hpu.edu.vn"
        # Auto-provision với role thấp nhất
        assert data["user"]["org_role"] == "member"

        # User đã được tạo trong đúng org
        result = await db_session.execute(
            select(User).where(User.email == "giangvien@hpu.edu.vn")
        )
        user = result.scalar_one()
        assert user.organization_id == org_google.id

    async def test_existing_user_logs_in_keeps_role(
        self, async_client, db_session, org_google, monkeypatch
    ):
        from app.core.security import hash_password

        existing = User(
            organization_id=org_google.id,
            email="truongphong@hpu.edu.vn",
            username="truongphong",
            full_name="Trưởng Phòng",
            hashed_password=hash_password("x-mat-khau"),
            org_role="admin",
        )
        db_session.add(existing)
        await db_session.commit()

        _mock_google(monkeypatch, "truongphong@hpu.edu.vn")
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
            headers={"X-Org-Slug": org_google.slug},
        )
        assert response.status_code == 200
        # Giữ nguyên role admin, không bị reset về member
        assert response.json()["data"]["user"]["org_role"] == "admin"

    async def test_wrong_domain_rejected_403(self, async_client, org_google, monkeypatch):
        _mock_google(monkeypatch, "hacker@gmail.com")
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
            headers={"X-Org-Slug": org_google.slug},
        )
        assert response.status_code == 403
        assert "hpu.edu.vn" in response.json()["message"]

    async def test_org_without_google_config_rejected(
        self, async_client, org_a, monkeypatch
    ):
        # org_a (fixture gốc) chưa cấu hình google_workspace_domain
        _mock_google(monkeypatch, "ai-do@hpu.edu.vn")
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
            headers={"X-Org-Slug": org_a.slug},
        )
        assert response.status_code == 422

    async def test_auto_provision_disabled_rejects_new_user(
        self, async_client, db_session, monkeypatch
    ):
        org = Organization(
            name="Org khóa provision",
            slug="khoa",
            settings={
                "google_workspace_domain": "hpu.edu.vn",
                "google_auto_provision": False,
            },
        )
        db_session.add(org)
        await db_session.commit()

        _mock_google(monkeypatch, "nguoi-moi@hpu.edu.vn")
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
            headers={"X-Org-Slug": "khoa"},
        )
        assert response.status_code == 403

    async def test_google_not_configured_returns_business_error(
        self, async_client, org_google
    ):
        # Không mock — GOOGLE_CLIENT_ID rỗng trong test env → lỗi nghiệp vụ rõ ràng
        response = await async_client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
            headers={"X-Org-Slug": org_google.slug},
        )
        assert response.status_code == 422
        assert "GOOGLE_CLIENT_ID" in response.json()["message"]


class TestCandidateGoogleLogin:
    HOST = "http://hpu.talentchart.hpu.edu.vn"

    async def test_any_gmail_creates_candidate_and_token(
        self, async_client, db_session, org_a, monkeypatch
    ):
        _mock_google(monkeypatch, "ungvien.moi@gmail.com", "Ứng Viên Mới")

        response = await async_client.post(
            f"{self.HOST}/api/v1/public/auth/google", json={"id_token": "fake"}
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["candidate_token"]
        assert data["candidate"]["pipeline_stage"] == "RECEIVED"

        result = await db_session.execute(
            select(Candidate).where(Candidate.email == "ungvien.moi@gmail.com")
        )
        candidate = result.scalar_one()
        assert candidate.organization_id == org_a.id
        assert candidate.source == "google_login"

    async def test_existing_candidate_reused(
        self, async_client, db_session, org_a, monkeypatch
    ):
        candidate = Candidate(
            organization_id=org_a.id,
            full_name="Đã Ứng Tuyển",
            email="datungtuyen@gmail.com",
            pipeline_stage="RECEIVED",
        )
        db_session.add(candidate)
        await db_session.commit()

        _mock_google(monkeypatch, "datungtuyen@gmail.com")
        response = await async_client.post(
            f"{self.HOST}/api/v1/public/auth/google", json={"id_token": "fake"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["candidate"]["id"] == str(candidate.id)
        assert response.json()["data"]["candidate"]["pipeline_stage"] == "RECEIVED"

    async def test_candidate_me_and_active_test(
        self, async_client, db_session, org_a, hr_manager_org_a, monkeypatch
    ):
        from tests.conftest import auth_headers

        _mock_google(monkeypatch, "xemtest@gmail.com")
        login = await async_client.post(
            f"{self.HOST}/api/v1/public/auth/google", json={"id_token": "fake"}
        )
        token = login.json()["data"]["candidate_token"]
        candidate_id = login.json()["data"]["candidate"]["id"]
        headers = {"Authorization": f"Bearer {token}"}

        # /me hoạt động
        me = await async_client.get(
            f"{self.HOST}/api/v1/public/candidates/me", headers=headers
        )
        assert me.status_code == 200
        assert me.json()["data"]["email"] == "xemtest@gmail.com"

        # Chưa có test → 404
        no_test = await async_client.get(
            f"{self.HOST}/api/v1/public/candidates/me/test", headers=headers
        )
        assert no_test.status_code == 404

        # HR gửi test (ứng viên đang RECEIVED → tự chuyển ASSESSMENT) → ứng viên thấy link
        await async_client.post(
            "/api/v1/test-links",
            json={"candidate_id": candidate_id},
            headers=auth_headers(hr_manager_org_a),
        )
        has_test = await async_client.get(
            f"{self.HOST}/api/v1/public/candidates/me/test", headers=headers
        )
        assert has_test.status_code == 200
        assert has_test.json()["data"]["token"]

    async def test_candidate_token_cannot_access_admin_api(
        self, async_client, org_a, monkeypatch
    ):
        # Token type=candidate KHÔNG vào được API quản trị (ADR-004)
        _mock_google(monkeypatch, "leo-thang@gmail.com")
        login = await async_client.post(
            f"{self.HOST}/api/v1/public/auth/google", json={"id_token": "fake"}
        )
        token = login.json()["data"]["candidate_token"]

        response = await async_client.get(
            "/api/v1/users", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    async def test_login_without_subdomain_404(self, async_client, org_a, monkeypatch):
        _mock_google(monkeypatch, "khongtenant@gmail.com")
        response = await async_client.post(
            "/api/v1/public/auth/google", json={"id_token": "fake"}
        )
        assert response.status_code == 404
