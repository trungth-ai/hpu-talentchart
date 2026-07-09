# Test nhịp sinh học (đơn vị)

from datetime import date

from app.services.epa.biorhythm import biorhythm_series, biorhythm_today


def test_birthday_all_zero():
    b = biorhythm_today(date(1990, 1, 1), date(1990, 1, 1))
    assert b == {"days_alive": 0, "physical": 0, "emotional": 0, "intellectual": 0}


def test_series_length_and_center():
    s = biorhythm_series(date(1990, 1, 1), date(2020, 1, 1), span=14)
    assert len(s) == 29
    assert s[14]["offset"] == 0
    assert s[0]["offset"] == -14 and s[-1]["offset"] == 14


def test_values_in_range():
    b = biorhythm_today(date(1985, 6, 15), date(2026, 7, 9))
    for k in ("physical", "emotional", "intellectual"):
        assert -100 <= b[k] <= 100
