# Test tử vi theo ngày (bảng daily_fortunes): đọc từ DB, cào bù hôm nay, xem ngày trước, cào lô.
# Cào mạng được MOCK (monkeypatch) — test chạy offline, không gọi lichngaytot thật.

from datetime import UTC, date, datetime, timedelta

from app.models.candidate import Candidate
from app.models.daily_fortune import DailyFortune
from app.services.epa import daily_fortune_store, fortune
from tests.conftest import auth_headers


class TestDailyFortuneStore:
    async def test_reads_from_db_without_scraping(self, db_session, monkeypatch):
        async def boom(*a, **k):
            raise AssertionError("Không được cào khi đã có dữ liệu / ngày quá khứ")

        monkeypatch.setattr(fortune, "scrape_lichngaytot", boom)
        d = date(2026, 7, 11)
        db_session.add(DailyFortune(fortune_date=d, kind="day", key="", excerpt="Ngày tốt"))
        db_session.add(
            DailyFortune(fortune_date=d, kind="zodiac_day", key="Tỵ", excerpt="Tuổi Tỵ")
        )
        await db_session.commit()

        # today > d → không cào bù, chỉ đọc DB
        out = await daily_fortune_store.get_daily_for(
            db_session, dia_chi="Tỵ", sign_code="CAPRICORN", on_date=d, today=d + timedelta(days=1)
        )
        assert out["date"] == "2026-07-11"
        assert out["day"]["excerpt"] == "Ngày tốt"
        assert out["zodiac_day"]["excerpt"] == "Tuổi Tỵ"
        assert out["horoscope_day"] is None  # chưa có trong DB

    async def test_lazy_scrape_today_when_missing(self, db_session, monkeypatch):
        d = date(2026, 7, 11)

        async def fake_scrape(dia_chi, sign_code, today):
            return {
                "day": {"url": "http://x/day", "excerpt": "Ngày cào bù"},
                "zodiac_day": {"url": "http://x/tuoi", "excerpt": f"Tuổi {dia_chi} cào bù"},
                "horoscope_day": {"url": "http://x/cung", "excerpt": f"Cung {sign_code} cào bù"},
            }

        monkeypatch.setattr(fortune, "scrape_lichngaytot", fake_scrape)
        out = await daily_fortune_store.get_daily_for(
            db_session, dia_chi="Tý", sign_code="ARIES", on_date=d, today=d
        )
        assert out["day"]["excerpt"] == "Ngày cào bù"
        assert "cào bù" in out["zodiac_day"]["excerpt"]
        # Đã lưu vào DB để lần sau khỏi cào
        row = await db_session.get(DailyFortune, (d, "zodiac_day", "Tý"))
        assert row is not None and "cào bù" in row.excerpt

    async def test_past_date_never_scrapes(self, db_session, monkeypatch):
        async def boom(*a, **k):
            raise AssertionError("Không được cào cho ngày quá khứ")

        monkeypatch.setattr(fortune, "scrape_lichngaytot", boom)
        out = await daily_fortune_store.get_daily_for(
            db_session,
            dia_chi="Tý",
            sign_code="ARIES",
            on_date=date(2026, 7, 1),
            today=date(2026, 7, 11),
        )
        assert out["day"] is None  # không có dữ liệu và KHÔNG cào

    async def test_scrape_and_store_all(self, db_session, monkeypatch):
        d = date(2026, 7, 11)

        async def fake_all(today):
            return [
                {"kind": "day", "key": "", "url": "u", "excerpt": "ngày"},
                {"kind": "zodiac_day", "key": "Tý", "url": "u", "excerpt": "tý"},
                {"kind": "horoscope_day", "key": "ARIES", "url": "u", "excerpt": "bạch dương"},
            ]

        monkeypatch.setattr(fortune, "scrape_all_daily", fake_all)
        n = await daily_fortune_store.scrape_and_store_all(db_session, d)
        assert n == 3
        row = await db_session.get(DailyFortune, (d, "horoscope_day", "ARIES"))
        assert row is not None and row.excerpt == "bạch dương"


class TestDailyFortuneEndpoint:
    async def _make_candidate(self, db_session, org_a) -> Candidate:
        c = Candidate(
            organization_id=org_a.id,
            full_name="Có Ngày Sinh",
            email="cons@mail.com",
            candidate_type="applicant",
            pipeline_stage="RECEIVED",
            epa_consent=True,
            epa_consent_at=datetime.now(UTC),
            birth_date=date(1990, 5, 20),
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)
        return c

    async def test_endpoint_reads_and_stores(
        self, async_client, db_session, hr_manager_org_a, org_a, monkeypatch
    ):
        c = await self._make_candidate(db_session, org_a)

        async def fake_scrape(dia_chi, sign_code, today):
            return {
                "day": {"url": "u", "excerpt": "nội dung ngày cào"},
                "zodiac_day": None,
                "horoscope_day": None,
            }

        monkeypatch.setattr(fortune, "scrape_lichngaytot", fake_scrape)
        r = await async_client.get(
            f"/api/v1/epa/candidates/{c.id}/lichngaytot", headers=auth_headers(hr_manager_org_a)
        )
        assert r.status_code == 200
        assert r.json()["data"]["day"]["excerpt"] == "nội dung ngày cào"

    async def test_endpoint_future_date_rejected(
        self, async_client, db_session, hr_manager_org_a, org_a
    ):
        c = await self._make_candidate(db_session, org_a)
        future = date.today().replace(year=date.today().year + 1).isoformat()
        r = await async_client.get(
            f"/api/v1/epa/candidates/{c.id}/lichngaytot?date={future}",
            headers=auth_headers(hr_manager_org_a),
        )
        assert r.status_code == 422
