# ★ Test parity DISC — so khớp bản port với code gốc SmartHire (ADR-001: ≥20 case)
# Load TRỰC TIẾP file legacy/smarthire-html/backend/{questions,disc}.py và so sánh
# output của cả 4 hàm trên nhiều bộ câu trả lời ngẫu nhiên (seeded).
# Nếu test này fail → BUG PORT, sửa app/services/disc_service.py, KHÔNG sửa thuật toán.

import importlib.util
import random
from pathlib import Path

import pytest

from app.services import disc_service

LEGACY_DIR = Path(__file__).resolve().parent.parent.parent / "legacy" / "smarthire-html" / "backend"


def _load_legacy():
    """Load module legacy: questions.py bình thường, disc.py phải vá dòng import."""
    spec = importlib.util.spec_from_file_location(
        "legacy_questions", LEGACY_DIR / "questions.py"
    )
    legacy_questions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy_questions)

    disc_source = (LEGACY_DIR / "disc.py").read_text(encoding="utf-8")
    # Bỏ dòng import gốc (from app.data.questions import ...) — inject trực tiếp
    disc_source = "\n".join(
        line for line in disc_source.splitlines() if "from app.data.questions" not in line
    )
    namespace = {
        "DISC_QUESTIONS": legacy_questions.DISC_QUESTIONS,
        "PERSONALITY_CATEGORIES": legacy_questions.PERSONALITY_CATEGORIES,
        "DISC_DESCRIPTIONS": legacy_questions.DISC_DESCRIPTIONS,
        "DISC_POSITION_PROFILES": legacy_questions.DISC_POSITION_PROFILES,
    }
    exec(compile(disc_source, str(LEGACY_DIR / "disc.py"), "exec"), namespace)
    return legacy_questions, namespace


LEGACY_QUESTIONS, LEGACY_DISC = _load_legacy()

# 25 bộ trả lời ngẫu nhiên (seed cố định — tái lập được) + các case biên
_rng = random.Random(42)


def _random_disc_answers(rng: random.Random) -> dict:
    answers = {}
    for i in range(len(LEGACY_QUESTIONS.DISC_QUESTIONS)):
        most = rng.randint(0, 3)
        least_choices = [j for j in range(4) if j != most]
        answers[str(i)] = {"most": most, "least": rng.choice(least_choices)}
    return answers


def _random_personality_answers(rng: random.Random) -> dict:
    total_qs = sum(len(c["qs"]) for c in LEGACY_QUESTIONS.PERSONALITY_CATEGORIES)
    return {str(i): rng.randint(1, 5) for i in range(total_qs)}


RANDOM_CASES = [
    (_random_disc_answers(_rng), _random_personality_answers(_rng)) for _ in range(25)
]

EDGE_CASES = [
    # Trả lời rỗng
    ({}, {}),
    # Toàn most=0 (thiên D), least=1
    ({str(i): {"most": 0, "least": 1} for i in range(40)}, {str(i): 3 for i in range(30)}),
    # Thiếu một nửa câu trả lời
    ({str(i): {"most": 2, "least": 3} for i in range(20)}, {str(i): 5 for i in range(15)}),
    # Index ngoài phạm vi (câu 999) + most/least = -1
    ({"999": {"most": 0, "least": 1}, "0": {"most": -1, "least": -1}}, {"0": 1}),
]

POSITIONS = ["Giảng viên CNTT", "Chuyên viên Tuyển sinh", "Trưởng Phòng Đào tạo", "Vị trí lạ", ""]


class TestDiscParity:
    def test_data_identical_to_legacy(self):
        """Dữ liệu câu hỏi/hằng số phải giống hệt bản gốc."""
        from app.data import disc_questions as ported

        assert ported.DISC_QUESTIONS == LEGACY_QUESTIONS.DISC_QUESTIONS
        assert ported.PERSONALITY_CATEGORIES == LEGACY_QUESTIONS.PERSONALITY_CATEGORIES
        assert ported.DISC_DESCRIPTIONS == LEGACY_QUESTIONS.DISC_DESCRIPTIONS
        assert ported.DISC_POSITION_PROFILES == LEGACY_QUESTIONS.DISC_POSITION_PROFILES

    @pytest.mark.parametrize("case_idx", range(len(RANDOM_CASES) + len(EDGE_CASES)))
    def test_scoring_matches_legacy(self, case_idx):
        """calculate_disc + calculate_personality khớp 100% với hệ cũ (29 case)."""
        all_cases = RANDOM_CASES + EDGE_CASES
        disc_answers, personality_answers = all_cases[case_idx]

        assert disc_service.calculate_disc(disc_answers) == LEGACY_DISC["calculate_disc"](
            disc_answers
        )
        assert disc_service.calculate_personality(
            personality_answers
        ) == LEGACY_DISC["calculate_personality"](personality_answers)

    @pytest.mark.parametrize("position", POSITIONS)
    def test_analysis_matches_legacy(self, position):
        """generate_analysis + generate_ai_interview_suggestions khớp với hệ cũ."""
        for disc_answers, personality_answers in RANDOM_CASES[:5] + EDGE_CASES[1:2]:
            disc_result = disc_service.calculate_disc(disc_answers)
            personality = disc_service.calculate_personality(personality_answers)

            assert disc_service.generate_analysis(
                disc_result, personality, position
            ) == LEGACY_DISC["generate_analysis"](disc_result, personality, position)
            assert disc_service.generate_ai_interview_suggestions(
                disc_result, personality, position
            ) == LEGACY_DISC["generate_ai_interview_suggestions"](
                disc_result, personality, position
            )

    def test_public_questions_never_leak_answer_key(self):
        """Câu hỏi public không được chứa mapping D/I/S/C (chống gian lận)."""
        public = disc_service.get_public_questions()
        for q in public["disc_questions"]:
            for opt in q["options"]:
                assert "d" not in opt
        assert len(public["disc_questions"]) == 40
        assert sum(len(c["qs"]) for c in public["personality_categories"]) == 30
