# Test flow bài test DISC: tạo link → làm bài → chấm điểm → pipeline TEST_DONE

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.candidate import Candidate
from app.models.test_session import TestSession
from tests.conftest import auth_headers

TEST_HOST = "http://hpu.talentchart.hpu.edu.vn"


@pytest.fixture
async def screening_candidate(db_session, org_a) -> Candidate:
    candidate = Candidate(
        organization_id=org_a.id,
        full_name="Ứng Viên Làm Test",
        email="lamtest@mail.com",
        position="Giảng viên CNTT",
        pipeline_stage="SCREENING",
    )
    db_session.add(candidate)
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


async def _create_link(client, candidate_id, user) -> dict:
    response = await client.post(
        "/api/v1/test-links",
        json={"candidate_id": str(candidate_id)},
        headers=auth_headers(user),
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _full_answers() -> dict:
    # 40 câu DISC (most=0, least=1) + 30 câu personality điểm 4
    return {
        "disc_answers": {str(i): {"most": 0, "least": 1} for i in range(40)},
        "personality_answers": {str(i): 4 for i in range(30)},
    }


class TestCreateTestLink:
    async def test_create_link_moves_screening_to_test_sent(
        self, async_client, db_session, hr_manager_org_a, screening_candidate
    ):
        data = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        assert "/test/" in data["test_url"]
        await db_session.refresh(screening_candidate)
        assert screening_candidate.pipeline_stage == "TEST_SENT"

    async def test_cannot_create_link_for_new_candidate(
        self, async_client, db_session, hr_manager_org_a, org_a
    ):
        # Pipeline tuần tự: NEW chưa qua SCREENING → không gửi test được
        candidate = Candidate(
            organization_id=org_a.id, full_name="Mới", email="moi@mail.com"
        )
        db_session.add(candidate)
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/test-links",
            json={"candidate_id": str(candidate.id)},
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 422

    async def test_resend_invalidates_old_link(
        self, async_client, hr_manager_org_a, screening_candidate
    ):
        first = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        second = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)

        # Link cũ bị vô hiệu → 404
        response = await async_client.get(
            f"{TEST_HOST}/api/v1/public/test/{first['token']}"
        )
        assert response.status_code == 404
        # Link mới hoạt động
        response = await async_client.get(
            f"{TEST_HOST}/api/v1/public/test/{second['token']}"
        )
        assert response.status_code == 200

    async def test_cross_tenant_candidate_404(
        self, async_client, db_session, hr_manager_org_b, screening_candidate
    ):
        response = await async_client.post(
            "/api/v1/test-links",
            json={"candidate_id": str(screening_candidate.id)},
            headers=auth_headers(hr_manager_org_b),
        )
        assert response.status_code == 404


class TestTakeTest:
    async def test_get_test_returns_questions_without_answer_key(
        self, async_client, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        response = await async_client.get(f"{TEST_HOST}/api/v1/public/test/{link['token']}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["candidate_name"] == screening_candidate.full_name
        assert len(data["disc_questions"]) == 40
        # Không leak mapping D/I/S/C
        assert all("d" not in opt for q in data["disc_questions"] for opt in q["options"])

    async def test_token_from_wrong_tenant_subdomain_404(
        self, async_client, org_b, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        # Token của org A mở trên subdomain org B → 404
        response = await async_client.get(
            f"http://alpha.talentchart.hpu.edu.vn/api/v1/public/test/{link['token']}"
        )
        assert response.status_code == 404

    async def test_submit_scores_and_moves_to_test_done(
        self, async_client, db_session, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)

        response = await async_client.post(
            f"{TEST_HOST}/api/v1/public/test/{link['token']}/submit",
            json=_full_answers(),
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        # most=0 toàn bộ → thiên D (theo thuật toán gốc SmartHire)
        assert data["disc_primary"] == "D"
        assert sum(data["disc_scores"].values()) in range(98, 103)  # ~100% sau làm tròn
        # Ứng viên KHÔNG nhận phân tích nội bộ
        assert "analysis" not in data
        assert "recommendation" not in data

        await db_session.refresh(screening_candidate)
        assert screening_candidate.pipeline_stage == "TEST_DONE"

    async def test_submit_twice_rejected(
        self, async_client, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        url = f"{TEST_HOST}/api/v1/public/test/{link['token']}/submit"
        first = await async_client.post(url, json=_full_answers())
        second = await async_client.post(url, json=_full_answers())
        assert first.status_code == 200
        assert second.status_code == 422

    async def test_expired_link_rejected(
        self, async_client, db_session, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        # Chỉnh expires_at về quá khứ
        result = await db_session.execute(
            select(TestSession).where(TestSession.token == link["token"])
        )
        session = result.scalar_one()
        session.expires_at = datetime.now(UTC) - timedelta(hours=1)
        await db_session.commit()

        response = await async_client.get(f"{TEST_HOST}/api/v1/public/test/{link['token']}")
        assert response.status_code == 422

    async def test_invalid_likert_rejected(
        self, async_client, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        response = await async_client.post(
            f"{TEST_HOST}/api/v1/public/test/{link['token']}/submit",
            json={"disc_answers": {}, "personality_answers": {"0": 9}},
        )
        assert response.status_code == 422


class TestAdminResult:
    async def test_admin_gets_full_result(
        self, async_client, hr_manager_org_a, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        await async_client.post(
            f"{TEST_HOST}/api/v1/public/test/{link['token']}/submit", json=_full_answers()
        )

        response = await async_client.get(
            f"/api/v1/test-links/candidates/{screening_candidate.id}/result",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # Bản HR có đầy đủ phân tích + gợi ý phỏng vấn
        assert data["analysis"]["recommendation_text"]
        assert data["ai_suggestions"]["suggested_questions"]
        assert isinstance(data["overall_score"], int)

    async def test_other_org_cannot_see_result(
        self, async_client, hr_manager_org_a, hr_manager_org_b, screening_candidate
    ):
        link = await _create_link(async_client, screening_candidate.id, hr_manager_org_a)
        await async_client.post(
            f"{TEST_HOST}/api/v1/public/test/{link['token']}/submit", json=_full_answers()
        )
        response = await async_client.get(
            f"/api/v1/test-links/candidates/{screening_candidate.id}/result",
            headers=auth_headers(hr_manager_org_b),
        )
        assert response.status_code == 404
