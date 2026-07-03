# Test module job_posts + public career page API (Sprint 4)

import pytest
from sqlalchemy import select

from app.models.candidate import Candidate
from app.models.job_post import JobPost
from tests.conftest import auth_headers
from tests.test_campaigns import campaign_org_a, campaign_org_b  # noqa: F401 — fixtures


@pytest.fixture
async def published_job_org_a(db_session, org_a) -> JobPost:
    job = JobPost(
        organization_id=org_a.id,
        title="Giảng viên Công nghệ thông tin",
        slug="giang-vien-cong-nghe-thong-tin",
        salary_min=15_000_000,
        salary_max=30_000_000,
        is_published=True,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


@pytest.fixture
async def draft_job_org_a(db_session, org_a) -> JobPost:
    job = JobPost(
        organization_id=org_a.id,
        title="Tin nháp chưa đăng",
        slug="tin-nhap",
        is_published=False,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job


class TestJobPostAdmin:
    async def test_create_auto_slug_from_vietnamese_title(
        self, async_client, hr_manager_org_a
    ):
        response = await async_client.post(
            "/api/v1/job-posts",
            json={"title": "Chuyên viên Đào tạo & Phát triển"},
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 201
        assert response.json()["data"]["slug"] == "chuyen-vien-dao-tao-phat-trien"
        assert response.json()["data"]["is_published"] is False

    async def test_duplicate_slug_same_org_409(
        self, async_client, hr_manager_org_a, published_job_org_a
    ):
        response = await async_client.post(
            "/api/v1/job-posts",
            json={
                "title": "Tin khác",
                "slug": published_job_org_a.slug,
            },
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 409
        assert response.json()["code"] == "DUPLICATE"

    async def test_same_slug_different_org_allowed(
        self, async_client, hr_manager_org_b, published_job_org_a
    ):
        # Slug chỉ unique TRONG org — org khác dùng lại được
        response = await async_client.post(
            "/api/v1/job-posts",
            json={"title": "Tin của org B", "slug": published_job_org_a.slug},
            headers=auth_headers(hr_manager_org_b),
        )
        assert response.status_code == 201

    async def test_publish_unpublish(
        self, async_client, db_session, hr_manager_org_a, draft_job_org_a
    ):
        response = await async_client.post(
            f"/api/v1/job-posts/{draft_job_org_a.id}/publish",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        await db_session.refresh(draft_job_org_a)
        assert draft_job_org_a.is_published is True
        assert draft_job_org_a.published_at is not None

    async def test_cannot_get_other_org_job_404(
        self, async_client, hr_manager_org_b, published_job_org_a
    ):
        response = await async_client.get(
            f"/api/v1/job-posts/{published_job_org_a.id}",
            headers=auth_headers(hr_manager_org_b),
        )
        assert response.status_code == 404


class TestPublicCareerPage:
    """API công khai theo subdomain — không cần đăng nhập."""

    async def test_public_list_only_published(
        self, async_client, published_job_org_a, draft_job_org_a
    ):
        response = await async_client.get(
            "http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs"
        )
        assert response.status_code == 200
        slugs = [j["slug"] for j in response.json()["data"]]
        assert published_job_org_a.slug in slugs
        assert draft_job_org_a.slug not in slugs  # tin nháp không hiện

    async def test_public_list_scoped_by_subdomain(
        self, async_client, org_b, published_job_org_a
    ):
        # Career page của org B không thấy tin của org A
        response = await async_client.get(
            "http://alpha.talentchart.hpu.edu.vn/api/v1/public/jobs"
        )
        assert response.status_code == 200
        assert response.json()["data"] == []

    async def test_public_without_tenant_404(self, async_client):
        # Domain chính (app.) không phải career page tenant
        response = await async_client.get("/api/v1/public/jobs")
        assert response.status_code == 404

    async def test_public_job_detail_by_slug(self, async_client, published_job_org_a):
        response = await async_client.get(
            f"http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs/{published_job_org_a.slug}"
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == published_job_org_a.title
        # Public response không lộ thông tin nội bộ
        assert "campaign_id" not in data
        assert "organization_id" not in data

    async def test_apply_creates_candidate_new_stage(
        self, async_client, db_session, org_a, published_job_org_a
    ):
        response = await async_client.post(
            f"http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs/{published_job_org_a.slug}/apply",
            json={
                "full_name": "Ứng Viên Career Page",
                "email": "apply@mail.com",
                "phone": "0912345678",
            },
        )
        assert response.status_code == 201

        result = await db_session.execute(
            select(Candidate).where(Candidate.email == "apply@mail.com")
        )
        candidate = result.scalar_one()
        assert candidate.pipeline_stage == "NEW"
        assert candidate.source == "career_page"
        assert candidate.organization_id == org_a.id  # đúng tenant theo subdomain
        assert candidate.position == published_job_org_a.title

    async def test_apply_with_epa_consent_stores_birth_data(
        self, async_client, db_session, published_job_org_a
    ):
        response = await async_client.post(
            f"http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs/{published_job_org_a.slug}/apply",
            json={
                "full_name": "Ứng Viên EPA",
                "email": "epa@mail.com",
                "epa_consent": True,
                "birth_date": "1995-08-20",
                "birth_time": "14:30",
                "birth_place": "Hải Phòng",
            },
        )
        assert response.status_code == 201
        result = await db_session.execute(
            select(Candidate).where(Candidate.email == "epa@mail.com")
        )
        candidate = result.scalar_one()
        assert candidate.epa_consent is True
        assert candidate.birth_time == "14:30"

    async def test_apply_birth_data_without_consent_rejected(
        self, async_client, published_job_org_a
    ):
        response = await async_client.post(
            f"http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs/{published_job_org_a.slug}/apply",
            json={
                "full_name": "Không Consent",
                "email": "noconsent@mail.com",
                "birth_date": "1995-08-20",
            },
        )
        assert response.status_code == 422

    async def test_duplicate_application_rejected(
        self, async_client, published_job_org_a
    ):
        payload = {"full_name": "Nộp Hai Lần", "email": "double@mail.com"}
        url = f"http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs/{published_job_org_a.slug}/apply"
        first = await async_client.post(url, json=payload)
        second = await async_client.post(url, json=payload)
        assert first.status_code == 201
        assert second.status_code == 422
        assert second.json()["code"] == "BUSINESS_RULE_ERROR"

    async def test_apply_to_unpublished_job_404(self, async_client, draft_job_org_a):
        response = await async_client.post(
            f"http://hpu.talentchart.hpu.edu.vn/api/v1/public/jobs/{draft_job_org_a.slug}/apply",
            json={"full_name": "X", "email": "x@mail.com"},
        )
        assert response.status_code == 404
