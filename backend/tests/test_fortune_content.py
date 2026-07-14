# Test tử vi theo KỲ (bảng fortune_content): period_key, đọc DB, cào bù kỳ hiện tại, cào lô.
# Cào mạng được MOCK (monkeypatch) — chạy offline, không gọi lichngaytot thật.

from datetime import UTC, date, datetime, timedelta

from app.models.candidate import Candidate
from app.models.fortune_content import FortuneContent
from app.services.epa import fortune
from app.services.epa import fortune_content_store as store
from tests.conftest import auth_headers

_ALL_CHI = ("Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi")
_ALL_CODES = (
    "ARIES", "TAURUS", "GEMINI", "CANCER", "LEO", "VIRGO",
    "LIBRA", "SCORPIO", "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
)


class TestPeriodKey:
    def test_period_keys(self):
        d = date(2026, 7, 13)
        iso = d.isocalendar()
        assert store.period_key_for("day", d) == "2026-07-13"
        assert store.period_key_for("week", d) == f"{iso.year}-W{iso.week:02d}"
        assert store.period_key_for("month", d) == "2026-07"
        assert store.period_key_for("year", d) == "2026"


class TestFortuneContentStore:
    async def test_reads_from_db_without_scraping(self, db_session, monkeypatch):
        async def boom(*a, **k):
            raise AssertionError("Không được cào khi kỳ quá khứ")

        monkeypatch.setattr(fortune, "scrape_lichngaytot", boom)
        d = date(2026, 7, 11)
        pkey = store.period_key_for("day", d)
        db_session.add(
            FortuneContent(
                period_type="day", period_key=pkey, kind="day", key="", excerpt="Ngày tốt"
            )
        )
        db_session.add(
            FortuneContent(
                period_type="day", period_key=pkey, kind="zodiac", key="Tỵ", excerpt="T Tỵ"
            )
        )
        await db_session.commit()

        out = await store.get_fortune(
            db_session, period_type="day", dia_chi="Tỵ", sign_code="CAPRICORN",
            on_date=d, today=d + timedelta(days=1),
        )
        assert out["period_key"] == "2026-07-11"
        assert out["day"]["excerpt"] == "Ngày tốt"
        assert out["zodiac"]["excerpt"] == "T Tỵ"
        assert out["horoscope"] is None

    async def test_lazy_scrape_current_day(self, db_session, monkeypatch):
        d = date(2026, 7, 11)

        async def fake(dia_chi, sign_code, today):
            return {
                "day": {"url": "u", "excerpt": "Ngày cào bù"},
                "zodiac_day": {"url": "u", "excerpt": f"Tuổi {dia_chi} cào bù"},
                "horoscope_day": {"url": "u", "excerpt": f"Cung {sign_code} cào bù"},
            }

        monkeypatch.setattr(fortune, "scrape_lichngaytot", fake)
        out = await store.get_fortune(
            db_session, period_type="day", dia_chi="Tý", sign_code="ARIES", on_date=d, today=d
        )
        assert out["day"]["excerpt"] == "Ngày cào bù"
        assert "cào bù" in out["zodiac"]["excerpt"]
        row = await db_session.get(FortuneContent, ("day", "2026-07-11", "zodiac", "Tý"))
        assert row is not None and "cào bù" in row.excerpt

    async def test_lazy_scrape_current_week(self, db_session, monkeypatch):
        d = date(2026, 7, 13)

        async def fake_period(period_type):
            assert period_type == "week"
            return [
                {"kind": "zodiac", "key": "Tý", "url": "u", "excerpt": "tuần tý"},
                {"kind": "horoscope", "key": "ARIES", "url": "u", "excerpt": "tuần bạch dương"},
            ]

        monkeypatch.setattr(fortune, "scrape_period", fake_period)
        out = await store.get_fortune(
            db_session, period_type="week", dia_chi="Tý", sign_code="ARIES", on_date=d, today=d
        )
        assert out["zodiac"]["excerpt"] == "tuần tý"
        assert out["horoscope"]["excerpt"] == "tuần bạch dương"
        wk = store.period_key_for("week", d)
        assert await db_session.get(FortuneContent, ("week", wk, "zodiac", "Tý")) is not None

    async def test_past_period_never_scrapes(self, db_session, monkeypatch):
        async def boom(*a, **k):
            raise AssertionError("Không cào kỳ quá khứ")

        monkeypatch.setattr(fortune, "scrape_period", boom)
        out = await store.get_fortune(
            db_session, period_type="month", dia_chi="Tý", sign_code="ARIES",
            on_date=date(2026, 5, 1), today=date(2026, 7, 13),
        )
        assert out["zodiac"] is None

    async def test_scrape_and_store_batch_week(self, db_session, monkeypatch):
        async def fake_period(period_type):
            return [{"kind": "zodiac", "key": "Tý", "url": "u", "excerpt": "tuần"}]

        monkeypatch.setattr(fortune, "scrape_period", fake_period)
        d = date(2026, 7, 13)
        n = await store.scrape_and_store(db_session, "week", d)
        assert n == 1
        wk = store.period_key_for("week", d)
        row = await db_session.get(FortuneContent, ("week", wk, "zodiac", "Tý"))
        assert row is not None and row.excerpt == "tuần"


class TestFortuneEndpoint:
    async def _make_candidate(self, db_session, org_a) -> Candidate:
        c = Candidate(
            organization_id=org_a.id, full_name="Có Ngày Sinh", email="cons@mail.com",
            candidate_type="applicant", pipeline_stage="RECEIVED",
            epa_consent=True, epa_consent_at=datetime.now(UTC), birth_date=date(1990, 5, 20),
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)
        return c

    async def test_endpoint_day_reads_and_stores(
        self, async_client, db_session, hr_manager_org_a, org_a, monkeypatch
    ):
        c = await self._make_candidate(db_session, org_a)

        async def fake(dia_chi, sign_code, today):
            return {
                "day": {"url": "u", "excerpt": "nội dung ngày"},
                "zodiac_day": None,
                "horoscope_day": None,
            }

        monkeypatch.setattr(fortune, "scrape_lichngaytot", fake)
        r = await async_client.get(
            f"/api/v1/epa/candidates/{c.id}/lichngaytot", headers=auth_headers(hr_manager_org_a)
        )
        assert r.status_code == 200
        assert r.json()["data"]["day"]["excerpt"] == "nội dung ngày"

    async def test_endpoint_week_period(
        self, async_client, db_session, hr_manager_org_a, org_a, monkeypatch
    ):
        c = await self._make_candidate(db_session, org_a)

        async def fake_period(period_type):
            recs = [
                {"kind": "zodiac", "key": k, "url": "u", "excerpt": f"z{k}"} for k in _ALL_CHI
            ]
            recs += [
                {"kind": "horoscope", "key": code, "url": "u", "excerpt": f"h{code}"}
                for code in _ALL_CODES
            ]
            return recs

        monkeypatch.setattr(fortune, "scrape_period", fake_period)
        r = await async_client.get(
            f"/api/v1/epa/candidates/{c.id}/lichngaytot?period=week",
            headers=auth_headers(hr_manager_org_a),
        )
        assert r.status_code == 200
        assert r.json()["data"]["period_type"] == "week"
        assert r.json()["data"]["zodiac"] is not None

    async def test_endpoint_invalid_period(self, async_client, db_session, hr_manager_org_a, org_a):
        c = await self._make_candidate(db_session, org_a)
        r = await async_client.get(
            f"/api/v1/epa/candidates/{c.id}/lichngaytot?period=decade",
            headers=auth_headers(hr_manager_org_a),
        )
        assert r.status_code == 422

    async def test_endpoint_future_rejected(
        self, async_client, db_session, hr_manager_org_a, org_a
    ):
        c = await self._make_candidate(db_session, org_a)
        future = date.today().replace(year=date.today().year + 1).isoformat()
        r = await async_client.get(
            f"/api/v1/epa/candidates/{c.id}/lichngaytot?date={future}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert r.status_code == 422
