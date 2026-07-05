# ★ Test parity EPA — so khớp bản port với code JS gốc Fortune HR (ADR-001: ≥20 case)
# Fixture epa_parity_fortune_hr.json được sinh bằng cách CHẠY TRỰC TIẾP code JS gốc
# (node tests/fixtures/generate_epa_fixture.mjs) — 300 case gồm case bắt buộc 1/1/1938
# và các mốc quanh Tết. Nếu fail → BUG PORT, sửa app/services/epa/, KHÔNG sửa thuật toán.

import json
import random
from datetime import date
from pathlib import Path

import pytest

from app.services.epa import canchi, compatibility, lunar, tamhop, team_suggest

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "epa_parity_fortune_hr.json").read_text(
        encoding="utf-8"
    )
)

# Map key JS (camelCase) → key Python (snake_case)
KEY_MAP = {
    "thienCan": "thien_can",
    "diaChi": "dia_chi",
    "conGiap": "con_giap",
    "emoji": "emoji",
    "tuoiAm": "tuoi_am",
    "napAm": "nap_am",
    "menh": "menh",
    "lunarYear": "lunar_year",
    "lunarMonth": "lunar_month",
    "lunarDay": "lunar_day",
}


class TestCanChiParity:
    def test_mandatory_case_1_1_1938_is_dinh_suu(self):
        """Case bắt buộc trong tài liệu: sinh 1/1/1938 dương → Đinh Sửu (năm 1937 âm)."""
        result = canchi.get_canchi_from_birth(1, 1, 1938)
        assert result["tuoi_am"] == "Đinh Sửu"
        assert result["lunar_year"] == 1937
        # Sai lầm cũ là tính theo năm dương → Mậu Dần
        assert result["tuoi_am"] != "Mậu Dần"

    @pytest.mark.parametrize(
        "case",
        FIXTURE,
        ids=lambda c: f"{c['input']['day']}-{c['input']['month']}-{c['input']['year']}",
    )
    def test_matches_original_js(self, case):
        """300 case so khớp từng field với output code JS gốc."""
        inp = case["input"]
        result = canchi.get_canchi_from_birth(inp["day"], inp["month"], inp["year"])
        for js_key, py_key in KEY_MAP.items():
            assert result[py_key] == case["expected"][js_key], (
                f"Lệch field {py_key} tại {inp['day']}/{inp['month']}/{inp['year']}: "
                f"port={result[py_key]!r} vs gốc={case['expected'][js_key]!r}"
            )

    def test_out_of_range_returns_solar_as_lunar(self):
        # Hành vi bản gốc: ngoài 1900-2100 trả nguyên ngày dương
        result = lunar.get_lunar_date(1850, 5, 10)
        assert result["lunar_year"] == 1850


class TestTamHopXung:
    def test_tam_hop_pair_scores_75(self):
        # Thân-Tý-Thìn cùng nhóm tam hợp
        assert tamhop.pair_score("Thân", "Tý") == 75
        assert tamhop.pair_score("Tý", "Thìn") == 75

    def test_xung_pair_scores_20(self):
        # Tý-Ngọ là cặp xung: 50 - 30 = 20
        assert tamhop.pair_score("Tý", "Ngọ") == 20
        assert tamhop.pair_score("Mão", "Dậu") == 20

    def test_neutral_pair_scores_50(self):
        assert tamhop.pair_score("Tý", "Sửu") == 50

    def test_same_chi_scores_45(self):
        # Quirk của bản gốc (giữ nguyên khi port): cùng chi vừa +25 (cùng nhóm tam hợp)
        # vừa −30 (cặp xung chứa chi đó match cả 2 người) → 50 + 25 − 30 = 45
        assert tamhop.pair_score("Tý", "Tý") == 45

    def test_all_pairs_within_bounds(self):
        for c1 in canchi.DIA_CHI:
            for c2 in canchi.DIA_CHI:
                assert 0 <= tamhop.pair_score(c1, c2) <= 100


class TestCompatibility:
    def test_tam_hop_couple(self):
        z1 = canchi.get_canchi_from_birth(15, 6, 1984)  # Giáp Tý
        z2 = canchi.get_canchi_from_birth(15, 6, 1992)  # Nhâm Thân
        assert z1["dia_chi"] == "Tý" and z2["dia_chi"] == "Thân"
        result = compatibility.compatibility_score(z1, z2)
        assert result["score"] == 75
        assert "Tam hợp: Rất tương hợp" in result["notes"]

    def test_xung_couple(self):
        z1 = canchi.get_canchi_from_birth(15, 6, 1984)  # Tý
        z2 = canchi.get_canchi_from_birth(15, 6, 1990)  # Ngọ
        result = compatibility.compatibility_score(z1, z2)
        assert result["score"] == 20
        assert "Xung: Dễ mâu thuẫn" in result["notes"]


class TestTeamSuggest:
    def _members(self, years):
        return [
            {
                "id": i,
                "full_name": f"NV{i}",
                "zodiac": canchi.get_canchi_from_birth(15, 6, y),
            }
            for i, y in enumerate(years)
        ]

    def test_returns_empty_when_not_enough_members(self):
        members = self._members([1984, 1985])
        assert team_suggest.suggest_teams(members, size=3) == []

    def test_returns_sorted_teams_with_seeded_rng(self):
        members = self._members([1984, 1985, 1986, 1987, 1988, 1990, 1992, 1996])
        teams = team_suggest.suggest_teams(members, size=3, rng=random.Random(42))
        assert len(teams) == 3
        # Xếp giảm dần theo điểm
        assert teams[0]["score"] >= teams[1]["score"] >= teams[2]["score"]
        # Điểm trong khoảng hợp lệ, đội đủ người
        for t in teams:
            assert 0 <= t["score"] <= 100
            assert len(t["members"]) == 3

    def test_tam_hop_team_scores_75(self):
        # Đội toàn Thân-Tý-Thìn → mọi cặp 75
        members = self._members([1984, 1992, 1988])  # Tý, Thân, Thìn
        chis = {m["zodiac"]["dia_chi"] for m in members}
        assert chis == {"Tý", "Thân", "Thìn"}
        teams = team_suggest.suggest_teams(members, size=3, rng=random.Random(1))
        assert teams[0]["score"] == 75


class TestTodayCanChi:
    def test_known_date(self):
        # 07/01/2000 là mốc ngày Giáp Tý của bản gốc
        result = canchi.get_today_canchi(today=date(2000, 1, 7))
        assert result["day_canchi"] == "Giáp Tý"
        # 07/01/2000 dương = 01/12/1999 âm → năm Kỷ Mão
        assert result["year_canchi"] == "Kỷ Mão"
