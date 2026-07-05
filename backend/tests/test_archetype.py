# Test 12 Personality Archetype — fusion DISC + Mệnh + Tam hợp (ADR-005)

from datetime import UTC, date, datetime

import pytest

from app.data.archetypes import ARCHETYPES, DISC_TO_ARCHETYPE
from app.models.candidate import Candidate
from app.models.test_session import TestSession
from app.services.epa import archetype
from tests.conftest import auth_headers


class TestFusionMapping:
    def test_all_16_disc_profiles_mapped(self):
        # 4 profile thuần + 12 tổ hợp — đủ 16, đều trỏ tới archetype hợp lệ
        assert len(DISC_TO_ARCHETYPE) == 16
        for code in DISC_TO_ARCHETYPE.values():
            assert code in ARCHETYPES

    def test_all_12_archetypes_reachable(self):
        # Mỗi archetype đều có ít nhất 1 đường vào từ DISC
        assert set(DISC_TO_ARCHETYPE.values()) == set(ARCHETYPES.keys())

    def test_disc_only_returns_base(self):
        result = archetype.compute_archetype("D")
        assert result["code"] == "CHALLENGER"
        assert result["used_eastern_data"] is False

    def test_unknown_profile_falls_back_to_primary(self):
        result = archetype.compute_archetype("D/X")
        assert result["code"] == "CHALLENGER"

    def test_tie_break_base_disc_wins(self):
        # S/C + Thổ + Sửu: GUARDIAN(base 2+Thổ1+Sửu1=4) vs ... base thắng rõ
        result = archetype.compute_archetype("S/C", menh="Thổ", dia_chi="Sửu")
        assert result["code"] == "GUARDIAN"

    def test_eastern_data_can_flip_archetype(self):
        # I/C: base VISIONARY(+2); đảo C/I → CRAFTSMAN(+1);
        # Mệnh Kim → CRAFTSMAN(+1)=2; chi Dậu → CRAFTSMAN(+1)=3 > VISIONARY=2
        without = archetype.compute_archetype("I/C")
        with_eastern = archetype.compute_archetype("I/C", menh="Kim", dia_chi="Dậu")
        assert without["code"] == "VISIONARY"
        assert with_eastern["code"] == "CRAFTSMAN"
        assert with_eastern["used_eastern_data"] is True

    def test_fusion_scores_transparent(self):
        result = archetype.compute_archetype("D/C", menh="Kim", dia_chi="Tý")
        # STRATEGIST: base 2 + Kim 1 + Tý 1 = 4
        assert result["fusion"]["scores"]["STRATEGIST"] == 4
        assert any("Mệnh Kim" in r for r in result["fusion"]["reasons"])


class TestArchetypeContent:
    def test_every_archetype_has_full_content(self):
        required = [
            "name_vi", "name_en", "tagline", "description", "strengths",
            "watchouts", "communication_dos", "communication_donts",
            "motivations", "stress_behavior", "improvement_tips", "university_fit",
        ]
        for code, data in ARCHETYPES.items():
            for field in required:
                assert data.get(field), f"{code} thiếu {field}"
            assert len(data["strengths"]) >= 3
            assert len(data["watchouts"]) >= 3

    def test_narrative_contains_key_elements(self):
        result = archetype.compute_archetype("C")
        text = archetype.build_narrative(
            "Nguyễn Văn A", result["archetype"], "C", {"D": 10, "I": 10, "S": 20, "C": 60}
        )
        assert "Nguyễn Văn A" in text
        assert "Nhà Phân Tích" in text
        assert "C (60%)" in text


@pytest.fixture
async def tested_employee(db_session, org_a) -> Candidate:
    """Nhân sự đã hoàn thành DISC (profile I/C) + có consent/birth_date."""
    candidate = Candidate(
        organization_id=org_a.id,
        full_name="Nguyễn Thị Fusion",
        email="fusion@hpu.edu.vn",
        candidate_type="employee",
        pipeline_stage="HIRED",
        epa_consent=True,
        epa_consent_at=datetime.now(UTC),
        # 15/6/1993 → Quý Dậu, mệnh Kim → đủ điều kiện flip I/C → CRAFTSMAN
        birth_date=date(1993, 6, 15),
    )
    db_session.add(candidate)
    await db_session.flush()
    db_session.add(
        TestSession(
            organization_id=org_a.id,
            candidate_id=candidate.id,
            token="tok-archetype-test",
            expires_at=datetime.now(UTC),
            is_used=True,
            completed_at=datetime.now(UTC),
            disc_profile="I/C",
            disc_primary="I",
            disc_secondary="C",
            disc_scores={"D": 10, "I": 45, "S": 10, "C": 35},
        )
    )
    await db_session.commit()
    await db_session.refresh(candidate)
    return candidate


class TestArchetypeAPI:
    async def test_archetype_without_disc_test_rejected(
        self, async_client, hr_manager_org_a, org_a, db_session
    ):
        candidate = Candidate(
            organization_id=org_a.id, full_name="Chưa Test", email="chuatest@mail.com"
        )
        db_session.add(candidate)
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/epa/candidates/{candidate.id}/archetype",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 422
        assert "bài test DISC" in response.json()["message"]

    async def test_archetype_behavioural_layer_no_eastern_toggle_needed(
        self, async_client, hr_manager_org_a, tested_employee
    ):
        # org_a KHÔNG bật Eastern Layer — archetype vẫn hoạt động (Behavioural Layer)
        response = await async_client.get(
            f"/api/v1/epa/candidates/{tested_employee.id}/archetype",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # Fusion dùng eastern data nội bộ (consent có sẵn): I/C + Kim + Dậu → CRAFTSMAN
        assert data["archetype"]["code"] == "CRAFTSMAN"
        assert data["used_eastern_data"] is True
        # Nhưng chi tiết fusion (nhắc Mệnh/Tam hợp) KHÔNG hiển thị khi toggle tắt
        assert "fusion" not in data
        assert data["narrative"]
        assert "tham khảo" in data["disclaimer"]

    async def test_archetype_without_consent_uses_disc_only(
        self, async_client, hr_manager_org_a, org_a, db_session
    ):
        candidate = Candidate(
            organization_id=org_a.id,
            full_name="Không Consent",
            email="noconsent-arch@mail.com",
        )
        db_session.add(candidate)
        await db_session.flush()
        db_session.add(
            TestSession(
                organization_id=org_a.id,
                candidate_id=candidate.id,
                token="tok-no-consent",
                expires_at=datetime.now(UTC),
                is_used=True,
                completed_at=datetime.now(UTC),
                disc_profile="I/C",
                disc_primary="I",
                disc_secondary="C",
                disc_scores={"D": 10, "I": 45, "S": 10, "C": 35},
            )
        )
        await db_session.commit()

        response = await async_client.get(
            f"/api/v1/epa/candidates/{candidate.id}/archetype",
            headers=auth_headers(hr_manager_org_a),
        )
        assert response.status_code == 200
        data = response.json()["data"]
        # Không có eastern data → base DISC: I/C → VISIONARY
        assert data["archetype"]["code"] == "VISIONARY"
        assert data["used_eastern_data"] is False

    async def test_cross_tenant_archetype_404(
        self, async_client, hr_manager_org_b, tested_employee
    ):
        response = await async_client.get(
            f"/api/v1/epa/candidates/{tested_employee.id}/archetype",
            headers=auth_headers(hr_manager_org_b),
        )
        assert response.status_code == 404
