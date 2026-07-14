# Test module campaigns — CRUD + tenant isolation (checklist /new-module)

import pytest

from app.models.campaign import Campaign
from tests.conftest import auth_headers


@pytest.fixture
async def campaign_org_a(db_session, org_a) -> Campaign:
    campaign = Campaign(
        organization_id=org_a.id,
        name="Tuyển giảng viên CNTT 2026",
        position="Giảng viên",
        salary_min=15_000_000,
        salary_max=25_000_000,
        status="open",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign


@pytest.fixture
async def campaign_org_b(db_session, org_b) -> Campaign:
    campaign = Campaign(
        organization_id=org_b.id,
        name="Tuyển HR Executive",
        position="HR Executive",
        status="open",
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign


class TestCampaignCRUD:
    async def test_create_campaign(self, async_client, hr_manager_org_a):
        response = await async_client.post(
            "/api/v1/campaigns",
            json={
                "name": "Tuyển chuyên viên đào tạo",
                "position": "Chuyên viên",
                "target_headcount": 2,
                "salary_min": 12_000_000,
                "salary_max": 18_000_000,
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["status"] == "draft"
        assert data["salary_min"] == 12_000_000  # Integer VNĐ, không float
        assert isinstance(data["salary_min"], int)
        assert "organization_id" not in data

    async def test_create_rejects_salary_max_below_min(
        self, async_client, hr_manager_org_a
    ):
        response = await async_client.post(
            "/api/v1/campaigns",
            json={
                "name": "X",
                "position": "Y",
                "salary_min": 20_000_000,
                "salary_max": 10_000_000,
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 422

    async def test_list_campaigns_paginated(
        self, async_client, hr_manager_org_a, campaign_org_a
    ):
        response = await async_client.get(
            "/api/v1/campaigns", headers=auth_headers(hr_manager_org_a)
        )
        assert response.status_code == 200
        body = response.json()
        assert body["meta"]["total"] == 1
        assert body["data"][0]["name"] == campaign_org_a.name

    async def test_update_campaign_partial(
        self, async_client, hr_manager_org_a, campaign_org_a
    ):
        response = await async_client.put(
            f"/api/v1/campaigns/{campaign_org_a.id}",
            json={"status": "closed"},
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "closed"
        # Field khác giữ nguyên (partial update)
        assert response.json()["data"]["name"] == campaign_org_a.name

    async def test_delete_is_soft_delete(
        self, async_client, db_session, hr_manager_org_a, campaign_org_a
    ):
        response = await async_client.delete(
            f"/api/v1/campaigns/{campaign_org_a.id}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        # Row vẫn còn trong DB, chỉ đổi status (KHÔNG hard delete)
        await db_session.refresh(campaign_org_a)
        assert campaign_org_a.status == "inactive"

    async def test_member_can_view_but_not_manage_campaigns(self, async_client, member_org_a):
        # Member = CHỈ XEM: GET được, nhưng tạo/sửa/xóa bị chặn (cần Recruiter+ / HR)
        listing = await async_client.get(
            "/api/v1/campaigns", headers=auth_headers(member_org_a)
        )
        assert listing.status_code == 200
        create = await async_client.post(
            "/api/v1/campaigns",
            json={"name": "X", "position": "Y"},
            headers=auth_headers(member_org_a),
        )
        assert create.status_code == 403


class TestCampaignIsolation:
    async def test_cannot_get_other_org_campaign_404(
        self, async_client, hr_manager_org_a, campaign_org_b
    ):
        response = await async_client.get(
            f"/api/v1/campaigns/{campaign_org_b.id}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 404  # KHÔNG 403

    async def test_list_does_not_include_other_org(
        self, async_client, hr_manager_org_a, campaign_org_a, campaign_org_b
    ):
        response = await async_client.get(
            "/api/v1/campaigns", headers=auth_headers(hr_manager_org_a)
        )
        names = [c["name"] for c in response.json()["data"]]
        assert campaign_org_b.name not in names

    async def test_cannot_update_other_org_campaign(
        self, async_client, hr_manager_org_a, campaign_org_b
    ):
        response = await async_client.put(
            f"/api/v1/campaigns/{campaign_org_b.id}",
            json={"name": "Bị chiếm quyền"},
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 404
