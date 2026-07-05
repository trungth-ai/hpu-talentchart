# Test EPA API — Eastern Layer toggle + consent gate + isolation

from datetime import UTC, date, datetime

import pytest

from app.models.candidate import Candidate
from app.models.organization import Organization
from tests.conftest import auth_headers


@pytest.fixture
async def org_eastern(db_session) -> Organization:
    """Org đã BẬT Eastern Layer."""
    org = Organization(
        name="Org Eastern",
        slug="eastern",
        settings={"eastern_layer_enabled": True},
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def hr_eastern(db_session, org_eastern):
    from tests.conftest import _make_user

    user = _make_user(org_eastern, "hr@eastern.vn")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _employee(org, name: str, birth: date, dept: str = "CNTT", consent: bool = True):
    return Candidate(
        organization_id=org.id,
        full_name=name,
        email=f"{name.lower().replace(' ', '.')}@hpu.edu.vn",
        candidate_type="employee",
        pipeline_stage="HIRED",
        department=dept,
        epa_consent=consent,
        epa_consent_at=datetime.now(UTC) if consent else None,
        birth_date=birth if consent else None,
    )


@pytest.fixture
async def emp_ty(db_session, org_eastern) -> Candidate:
    # 15/6/1984 → Giáp Tý
    emp = _employee(org_eastern, "Nguyen Van Ty", date(1984, 6, 15))
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


@pytest.fixture
async def emp_than(db_session, org_eastern) -> Candidate:
    # 15/6/1992 → Nhâm Thân (tam hợp với Tý)
    emp = _employee(org_eastern, "Tran Thi Than", date(1992, 6, 15))
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp


class TestEasternLayerToggle:
    async def test_org_without_eastern_layer_blocked(
        self, async_client, hr_manager_org_a
    ):
        # org_a mặc định eastern_layer_enabled=False → mọi endpoint EPA bị chặn
        response = await async_client.get(
            "/api/v1/epa/today", headers=auth_headers(hr_manager_org_a)
        )
        assert response.status_code == 422
        assert "Eastern Layer" in response.json()["message"]

    async def test_org_with_eastern_layer_allowed(self, async_client, hr_eastern):
        response = await async_client.get(
            "/api/v1/epa/today", headers=auth_headers(hr_eastern)
        )
        assert response.status_code == 200
        assert response.json()["data"]["year_canchi"]


class TestCandidateZodiac:
    async def test_zodiac_of_consented_employee(self, async_client, hr_eastern, emp_ty):
        response = await async_client.get(
            f"/api/v1/epa/candidates/{emp_ty.id}/zodiac",
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["zodiac"]["tuoi_am"] == "Giáp Tý"
        assert data["zodiac"]["menh"] == "Kim"  # Giáp Tý → Hải Trung Kim
        # Luôn kèm disclaimer nghiệp vụ
        assert "tham khảo" in data["disclaimer"]

    async def test_zodiac_without_consent_blocked(
        self, async_client, db_session, org_eastern, hr_eastern
    ):
        emp = _employee(org_eastern, "Khong Consent", date(1990, 1, 1), consent=False)
        db_session.add(emp)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/epa/candidates/{emp.id}/zodiac",
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 422
        assert "opt-in" in response.json()["message"]

    async def test_cross_tenant_zodiac_404(
        self, async_client, hr_eastern, db_session, org_a
    ):
        emp_other = _employee(org_a, "Nguoi Org Khac", date(1990, 1, 1))
        db_session.add(emp_other)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/epa/candidates/{emp_other.id}/zodiac",
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 404


class TestCompatibility:
    async def test_tam_hop_pair(self, async_client, hr_eastern, emp_ty, emp_than):
        response = await async_client.get(
            "/api/v1/epa/compatibility",
            params={"candidate1_id": str(emp_ty.id), "candidate2_id": str(emp_than.id)},
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["score"] == 75
        assert "Tam hợp: Rất tương hợp" in data["notes"]

    async def test_same_person_rejected(self, async_client, hr_eastern, emp_ty):
        response = await async_client.get(
            "/api/v1/epa/compatibility",
            params={"candidate1_id": str(emp_ty.id), "candidate2_id": str(emp_ty.id)},
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 422


class TestTeamSuggest:
    async def test_suggest_teams(
        self, async_client, db_session, org_eastern, hr_eastern
    ):
        years = [1984, 1985, 1986, 1988, 1990, 1992]
        for i, y in enumerate(years):
            db_session.add(_employee(org_eastern, f"NV So {i}", date(y, 6, 15)))
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/epa/team-suggest",
            json={"size": 3},
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["eligible_count"] == 6
        assert len(data["teams"]) == 3
        assert data["teams"][0]["score"] >= data["teams"][-1]["score"]

    async def test_department_filter(
        self, async_client, db_session, org_eastern, hr_eastern
    ):
        db_session.add(_employee(org_eastern, "CNTT Mot", date(1984, 6, 15), dept="CNTT"))
        db_session.add(_employee(org_eastern, "CNTT Hai", date(1988, 6, 15), dept="CNTT"))
        db_session.add(_employee(org_eastern, "Ke Toan", date(1990, 6, 15), dept="KT"))
        await db_session.commit()

        response = await async_client.post(
            "/api/v1/epa/team-suggest",
            json={"size": 2, "department": "CNTT"},
            headers=auth_headers(hr_eastern),
        )
        assert response.json()["data"]["eligible_count"] == 2

    async def test_not_enough_members(self, async_client, hr_eastern, emp_ty):
        response = await async_client.post(
            "/api/v1/epa/team-suggest",
            json={"size": 5},
            headers=auth_headers(hr_eastern),
        )
        assert response.status_code == 200
        assert response.json()["data"]["teams"] == []
