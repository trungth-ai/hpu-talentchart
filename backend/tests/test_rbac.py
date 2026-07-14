# Test phân quyền chức năng (RBAC): Recruiter = tuyển dụng (KHÔNG nhân sự / xóa / quản trị),
# Member = CHỈ XEM. (HR Manager / Admin đã có test ở test_candidates, test_admin.)

import pytest

from app.models.candidate import Candidate
from app.models.user import User
from tests.conftest import _make_user, auth_headers


@pytest.fixture
async def recruiter_org_a(db_session, org_a) -> User:
    u = _make_user(org_a, "recruiter.a@hpu.edu.vn", org_role="recruiter")
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.fixture
async def applicant_a(db_session, org_a) -> Candidate:
    c = Candidate(
        organization_id=org_a.id,
        full_name="Ứng viên A",
        email="uv.a@mail.com",
        candidate_type="applicant",
        pipeline_stage="RECEIVED",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


@pytest.fixture
async def employee_a(db_session, org_a) -> Candidate:
    c = Candidate(
        organization_id=org_a.id,
        full_name="Nhân sự A",
        email="ns.a@mail.com",
        candidate_type="employee",
        pipeline_stage="HIRED",
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c


class TestRecruiter:
    async def test_can_create_applicant(self, async_client, recruiter_org_a):
        r = await async_client.post(
            "/api/v1/candidates",
            json={"full_name": "UV mới", "email": "uvmoi@mail.com", "candidate_type": "applicant"},
            headers=auth_headers(recruiter_org_a),
        )
        assert r.status_code == 201

    async def test_cannot_create_employee(self, async_client, recruiter_org_a):
        r = await async_client.post(
            "/api/v1/candidates",
            json={"full_name": "NS mới", "email": "nsmoi@mail.com", "candidate_type": "employee"},
            headers=auth_headers(recruiter_org_a),
        )
        assert r.status_code == 403

    async def test_cannot_edit_employee(self, async_client, recruiter_org_a, employee_a):
        r = await async_client.put(
            f"/api/v1/candidates/{employee_a.id}",
            json={"position": "X"},
            headers=auth_headers(recruiter_org_a),
        )
        assert r.status_code == 403

    async def test_cannot_delete_candidate(self, async_client, recruiter_org_a, applicant_a):
        r = await async_client.delete(
            f"/api/v1/candidates/{applicant_a.id}", headers=auth_headers(recruiter_org_a)
        )
        assert r.status_code == 403

    async def test_can_transition_applicant(self, async_client, recruiter_org_a, applicant_a):
        r = await async_client.post(
            f"/api/v1/candidates/{applicant_a.id}/transition",
            json={"target_stage": "ASSESSMENT"},
            headers=auth_headers(recruiter_org_a),
        )
        assert r.status_code == 200

    async def test_cannot_view_users(self, async_client, recruiter_org_a):
        # /users là require_hr_manager (>=30) → recruiter (20) bị 403
        r = await async_client.get("/api/v1/users", headers=auth_headers(recruiter_org_a))
        assert r.status_code == 403


class TestMember:
    async def test_can_view_candidates(self, async_client, member_org_a, applicant_a):
        r = await async_client.get("/api/v1/candidates", headers=auth_headers(member_org_a))
        assert r.status_code == 200

    async def test_cannot_create_candidate(self, async_client, member_org_a):
        r = await async_client.post(
            "/api/v1/candidates",
            json={"full_name": "X", "email": "x2@mail.com"},
            headers=auth_headers(member_org_a),
        )
        assert r.status_code == 403

    async def test_cannot_send_test(self, async_client, member_org_a, applicant_a):
        r = await async_client.post(
            "/api/v1/test-links",
            json={"candidate_id": str(applicant_a.id)},
            headers=auth_headers(member_org_a),
        )
        assert r.status_code == 403
