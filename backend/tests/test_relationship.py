# Test quan hệ tuổi truyền thống (trung tính giới) — phủ ĐỦ 12x12 cặp con giáp.

from app.services.epa.compatibility import relationship

DIA_CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]


def test_relationship_covers_all_144_pairs():
    for a in DIA_CHI:
        for b in DIA_CHI:
            r = relationship(a, b)
            assert r["name"], f"thiếu quan hệ {a}-{b}"
            assert r["description"]


def test_relationship_known_cases():
    assert relationship("Thân", "Tý")["name"] == "Tam hợp"
    assert relationship("Tý", "Sửu")["name"] == "Lục hợp (nhị hợp)"
    assert relationship("Tý", "Ngọ")["name"] == "Lục xung"
    assert relationship("Tý", "Mùi")["name"] == "Lục hại"
    assert relationship("Tý", "Tý")["name"] == "Cùng tuổi"
    # Dần/Tỵ/Ngọ (sách thiếu mô tả hôn nhân) vẫn có quan hệ tuổi đầy đủ:
    assert relationship("Dần", "Ngọ")["name"] == "Tam hợp"
    assert relationship("Tỵ", "Thân")["name"] == "Lục hợp (nhị hợp)"
