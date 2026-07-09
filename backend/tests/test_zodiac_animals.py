# Test dữ liệu tính cách 12 con giáp (đơn vị)

from app.data.zodiac_animals import ZODIAC_ANIMALS, get_animal_by_dia_chi

DIA_CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


def test_all_12_animals_present_and_complete():
    assert len(ZODIAC_ANIMALS) == 12
    for dc in DIA_CHI:
        a = get_animal_by_dia_chi(dc)
        assert a is not None, f"thiếu địa chi {dc}"
        for field in ("animal", "personality", "strengths", "weaknesses", "careers"):
            assert a.get(field), f"{dc} thiếu {field}"


def test_lookup_unknown_returns_none():
    assert get_animal_by_dia_chi("Không") is None
