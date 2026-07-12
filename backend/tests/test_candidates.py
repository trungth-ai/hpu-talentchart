# Test module candidates — pipeline 7 trạng thái tuần tự + EPA consent + isolation

import pytest

from app.models.candidate import Candidate
from tests.conftest import auth_headers
from tests.test_campaigns import campaign_org_a, campaign_org_b  # noqa: F401 — fixtures


@pytest.fixture
async def candidate_org_a(db_session, org_a) -> Candidate:
    candidate = Candidate(
        organization_id=org_a.id,
        full_name="Nguyễn Văn Ứng",
        email="ungvien@mail.com",
        candidate_type="applicant",
        pipeline_stage="NEW",
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


@pytest.fixture
async def candidate_org_b(db_session, org_b) -> Candidate:
    candidate = Candidate(
        organization_id=org_b.id,
        full_name="Trần Thị B",
        email="b@mail.com",
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


async def _transition(client, candidate_id, stage, user):
    return await client.post(
        f"/api/v1/candidates/{candidate_id}/transition",
        json={"target_stage": stage},
        headers=auth_headers(user),
    )


class TestPipelineStateMachine:
    """Critical Business Rule (ADR-007): đi tiến tuần tự; Từ chối được ở bất kỳ bước."""

    async def test_full_sequential_flow_to_hired(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        for stage in ("SCREENING", "TEST_SENT", "TEST_DONE", "INTERVIEW", "DECISION", "HIRED"):
            response = await _transition(
                async_client, candidate_org_a.id, stage, hr_manager_org_a
            )
            assert response.status_code == 200, f"Chuyển sang {stage} thất bại"
            assert response.json()["data"]["pipeline_stage"] == stage

    async def test_cannot_skip_stage(self, async_client, hr_manager_org_a, candidate_org_a):
        # NEW → INTERVIEW là nhảy cóc → 422
        response = await _transition(
            async_client, candidate_org_a.id, "INTERVIEW", hr_manager_org_a
        )
        assert response.status_code == 422
        assert response.json()["code"] == "BUSINESS_RULE_ERROR"

    async def test_cannot_go_backward(self, async_client, hr_manager_org_a, candidate_org_a):
        await _transition(async_client, candidate_org_a.id, "SCREENING", hr_manager_org_a)
        response = await _transition(
            async_client, candidate_org_a.id, "NEW", hr_manager_org_a
        )
        assert response.status_code == 422

    async def test_decision_can_reject(self, async_client, hr_manager_org_a, candidate_org_a):
        for stage in ("SCREENING", "TEST_SENT", "TEST_DONE", "INTERVIEW", "DECISION"):
            await _transition(async_client, candidate_org_a.id, stage, hr_manager_org_a)
        response = await _transition(
            async_client, candidate_org_a.id, "REJECTED", hr_manager_org_a
        )
        assert response.status_code == 200
        assert response.json()["data"]["pipeline_stage"] == "REJECTED"

    async def test_can_reject_from_any_stage(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        # ADR-007: Từ chối ngay từ NEW (không cần đi hết pipeline)
        response = await _transition(
            async_client, candidate_org_a.id, "REJECTED", hr_manager_org_a
        )
        assert response.status_code == 200
        assert response.json()["data"]["pipeline_stage"] == "REJECTED"
        # REJECTED là trạng thái kết thúc → không chuyển tiếp được nữa
        after = await _transition(
            async_client, candidate_org_a.id, "SCREENING", hr_manager_org_a
        )
        assert after.status_code == 422

    async def test_can_reject_from_middle_stage(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        # Từ chối từ giữa pipeline (TEST_SENT) — bỏ qua TEST_DONE/INTERVIEW/DECISION
        for stage in ("SCREENING", "TEST_SENT"):
            await _transition(async_client, candidate_org_a.id, stage, hr_manager_org_a)
        response = await _transition(
            async_client, candidate_org_a.id, "REJECTED", hr_manager_org_a
        )
        assert response.status_code == 200
        assert response.json()["data"]["pipeline_stage"] == "REJECTED"

    async def test_still_cannot_hire_early(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        # HIRED vẫn CHỈ vào được từ DECISION — nới REJECTED KHÔNG mở HIRED sớm
        await _transition(async_client, candidate_org_a.id, "SCREENING", hr_manager_org_a)
        response = await _transition(
            async_client, candidate_org_a.id, "HIRED", hr_manager_org_a
        )
        assert response.status_code == 422

    async def test_terminal_stage_cannot_move(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        for stage in ("SCREENING", "TEST_SENT", "TEST_DONE", "INTERVIEW", "DECISION", "HIRED"):
            await _transition(async_client, candidate_org_a.id, stage, hr_manager_org_a)
        response = await _transition(
            async_client, candidate_org_a.id, "REJECTED", hr_manager_org_a
        )
        assert response.status_code == 422

    async def test_invalid_stage_rejected(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        response = await _transition(
            async_client, candidate_org_a.id, "BAY_MAU", hr_manager_org_a
        )
        assert response.status_code == 422

    async def test_create_cannot_set_pipeline_stage(
        self, async_client, hr_manager_org_a
    ):
        # Client gửi pipeline_stage khi tạo → bị bỏ qua, luôn bắt đầu từ NEW
        response = await async_client.post(
            "/api/v1/candidates",
            json={
                "full_name": "Hacker Pipeline",
                "email": "hp@mail.com",
                "pipeline_stage": "HIRED",
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 201
        assert response.json()["data"]["pipeline_stage"] == "NEW"


class TestEPAConsent:
    """NĐ 13/2023: dữ liệu ngày/giờ/nơi sinh chỉ lưu khi opt-in."""

    async def test_birth_data_without_consent_rejected(
        self, async_client, hr_manager_org_a
    ):
        response = await async_client.post(
            "/api/v1/candidates",
            json={
                "full_name": "Không Consent",
                "email": "kc@mail.com",
                "birth_date": "2000-03-15",
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 422

    async def test_birth_data_with_consent_accepted(
        self, async_client, hr_manager_org_a
    ):
        response = await async_client.post(
            "/api/v1/candidates",
            json={
                "full_name": "Có Consent",
                "email": "cc@mail.com",
                "epa_consent": True,
                "birth_date": "1938-01-01",
                "birth_time": "07:30",
                "birth_place": "Hải Phòng",
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 201
        assert response.json()["data"]["epa_consent"] is True
        # Dữ liệu sinh KHÔNG trả về trong response (nhạy cảm)
        assert "birth_date" not in response.json()["data"]

    async def test_delete_epa_data_endpoint(
        self, async_client, db_session, hr_manager_org_a, org_a
    ):
        from datetime import UTC, date, datetime

        candidate = Candidate(
            organization_id=org_a.id,
            full_name="Xóa EPA",
            email="xoa@mail.com",
            epa_consent=True,
            epa_consent_at=datetime.now(UTC),
            birth_date=date(1990, 5, 20),
            birth_time="10:00",
            birth_place="Hà Nội",
        )
        db_session.add(candidate)
        await db_session.commit()
        await db_session.refresh(candidate)

        response = await async_client.delete(
            f"/api/v1/candidates/{candidate.id}/epa-data",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        await db_session.refresh(candidate)
        assert candidate.epa_consent is False
        assert candidate.birth_date is None
        assert candidate.birth_time is None
        assert candidate.birth_place is None


class TestCandidateCRUD:
    async def test_stats_by_pipeline_stage(
        self, async_client, hr_manager_org_a, candidate_org_a
    ):
        response = await async_client.get(
            "/api/v1/candidates/stats", headers=auth_headers(hr_manager_org_a)
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["NEW"] == 1
        assert data["HIRED"] == 0

    async def test_soft_delete(
        self, async_client, db_session, hr_manager_org_a, candidate_org_a
    ):
        response = await async_client.delete(
            f"/api/v1/candidates/{candidate_org_a.id}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        await db_session.refresh(candidate_org_a)
        assert candidate_org_a.status == "inactive"

    async def test_candidate_type_validated(self, async_client, hr_manager_org_a):
        response = await async_client.post(
            "/api/v1/candidates",
            json={"full_name": "X", "email": "x@mail.com", "candidate_type": "alien"},
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 422


class TestCandidateIsolation:
    async def test_cannot_get_other_org_candidate_404(
        self, async_client, hr_manager_org_a, candidate_org_b
    ):
        response = await async_client.get(
            f"/api/v1/candidates/{candidate_org_b.id}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 404

    async def test_cannot_assign_other_org_campaign(
        self, async_client, hr_manager_org_a, campaign_org_b  # noqa: F811
    ):
        # IDOR qua foreign key: gán candidate vào campaign của org khác → 404
        response = await async_client.post(
            "/api/v1/candidates",
            json={
                "full_name": "IDOR Test",
                "email": "idor@mail.com",
                "campaign_id": str(campaign_org_b.id),
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 404

    async def test_stats_only_counts_own_org(
        self, async_client, hr_manager_org_a, candidate_org_a, candidate_org_b
    ):
        response = await async_client.get(
            "/api/v1/candidates/stats", headers=auth_headers(hr_manager_org_a)
        )
        assert response.json()["data"]["NEW"] == 1  # không đếm org B
