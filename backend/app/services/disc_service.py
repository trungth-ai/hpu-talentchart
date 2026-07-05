# ★ DISC Engine — PORT NGUYÊN XI từ SmartHire (legacy/smarthire-html/backend/disc.py)
# Nguồn gốc: D:/PROJECT/hpu-smart-hire/hpu-smarthire/backend/app/services/disc.py
#
# QUY TẮC PORT (CLAUDE.md): giữ nguyên công thức tính điểm — nếu test parity lệch
# kết quả so với hệ cũ thì đó là BUG PORT, sửa file này chứ không sửa thuật toán.
# Thay đổi duy nhất so với bản gốc: import path + type hints hiện đại (không đổi logic).

from typing import Any

from app.data.disc_questions import (
    DISC_DESCRIPTIONS,
    DISC_POSITION_PROFILES,
    DISC_QUESTIONS,
    PERSONALITY_CATEGORIES,
)


def calculate_disc(disc_answers: dict[str, dict[str, int]]) -> dict[str, Any]:
    """Tính điểm DISC từ câu trả lời most/least — port nguyên xi từ SmartHire."""
    scores = {"D": 0, "I": 0, "S": 0, "C": 0}
    neg = {"D": 0, "I": 0, "S": 0, "C": 0}

    for qi_str, ans in disc_answers.items():
        qi = int(qi_str)
        if qi >= len(DISC_QUESTIONS):
            continue
        q = DISC_QUESTIONS[qi]
        most_idx = ans.get("most", -1)
        least_idx = ans.get("least", -1)
        if most_idx >= 0 and most_idx < len(q["options"]):
            scores[q["options"][most_idx]["d"]] += 1
        if least_idx >= 0 and least_idx < len(q["options"]):
            neg[q["options"][least_idx]["d"]] += 1

    net = {d: scores[d] - neg[d] * 0.5 for d in "DISC" if d in scores}
    min_val = min(net.values()) if net else 0
    shifted = {d: net[d] - min_val for d in net}
    total = sum(shifted.values()) or 1
    pct = {d: round((shifted[d] / total) * 100) for d in shifted}

    sorted_items = sorted(pct.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_items[0][0]
    secondary = sorted_items[1][0]

    profile = f"{primary}/{secondary}" if pct[secondary] >= (pct[primary] * 0.7) else primary

    return {
        "disc_scores": pct,
        "disc_primary": primary,
        "disc_secondary": secondary,
        "disc_profile": profile,
    }


def calculate_personality(personality_answers: dict[str, int]) -> dict[str, float]:
    """Tính điểm 9 nhóm tính cách (Likert 1-5) — port nguyên xi từ SmartHire."""
    cat_scores = {}
    q_idx = 0
    for cat in PERSONALITY_CATEGORIES:
        total = 0
        for _ in cat["qs"]:
            val = personality_answers.get(str(q_idx), 3)
            total += val
            q_idx += 1
        cat_scores[cat["key"]] = round((total / (len(cat["qs"]) * 5)) * 100)
    return cat_scores


def generate_analysis(
    disc_result: dict[str, Any], personality_scores: dict[str, float], position: str
) -> dict[str, Any]:
    """Phân tích tổng hợp + khuyến nghị — port nguyên xi từ SmartHire."""
    primary = disc_result["disc_primary"]
    profile = disc_result["disc_profile"]
    desc = DISC_DESCRIPTIONS.get(primary, {})

    avg_personality = round(sum(personality_scores.values()) / max(len(personality_scores), 1))

    # Position fit analysis
    position_fit = None
    for pp in DISC_POSITION_PROFILES:
        if any(kw in position for kw in pp["pos"].split(" / ")[0].split(" — ")[0].split()):
            position_fit = pp
            break

    fit_score = 0
    if position_fit:
        fit_profiles = [p.strip() for p in position_fit["fit"].split(",")]
        if profile in fit_profiles:
            fit_score = 90
        elif primary in fit_profiles:
            fit_score = 75
        elif disc_result["disc_secondary"] in [p[0] for p in fit_profiles if len(p) == 1]:
            fit_score = 60
        else:
            fit_score = 40
    else:
        fit_score = 70  # default

    # Recommendation
    overall_score = round(
        avg_personality * 0.5
        + fit_score * 0.3
        + min(disc_result["disc_scores"].get(primary, 0), 100) * 0.2
    )

    if avg_personality >= 75 and fit_score >= 70:
        recommendation = "fit"
        rec_text = "PHÙ HỢP — Mời Phỏng vấn Vòng tiếp theo"
    elif avg_personality >= 55:
        recommendation = "caution"
        rec_text = "XEM XÉT — Cần Phỏng vấn Đánh giá Thêm"
    else:
        recommendation = "review"
        rec_text = "LƯU Ý — Cần Đánh giá Cẩn thận"

    # Strengths & weaknesses from personality
    strong_cats = sorted(personality_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    weak_cats = sorted(personality_scores.items(), key=lambda x: x[1])[:2]

    return {
        "disc_description": desc,
        "position_fit": position_fit,
        "fit_score": fit_score,
        "overall_score": overall_score,
        "recommendation": recommendation,
        "recommendation_text": rec_text,
        "avg_personality": avg_personality,
        "strong_categories": [{"key": k, "score": v} for k, v in strong_cats],
        "weak_categories": [{"key": k, "score": v} for k, v in weak_cats],
    }


def generate_ai_interview_suggestions(
    disc_result: dict[str, Any], personality_scores: dict[str, float], position: str
) -> dict[str, Any]:
    """Gợi ý câu hỏi phỏng vấn theo profile DISC — port nguyên xi từ SmartHire."""
    primary = disc_result["disc_primary"]
    profile = disc_result["disc_profile"]

    suggestions: dict[str, Any] = {
        "focus_areas": [],
        "suggested_questions": [],
        "red_flags_to_watch": [],
        "behavioral_patterns": [],
    }

    # Based on DISC primary
    disc_questions_map = {
        "D": {
            "focus": [
                "Kiểm tra khả năng lắng nghe và làm việc nhóm",
                "Đánh giá sự kiên nhẫn với quy trình",
            ],
            "questions": [
                "Kể về lần gần nhất bạn phải nhường nhịn trong một quyết định nhóm. "
                "Bạn cảm thấy thế nào?",
                "Khi một đồng nghiệp tiến hành công việc chậm hơn mong đợi, bạn phản ứng ra sao?",
                "Bạn xử lý thế nào khi cấp trên đưa ra quyết định bạn không đồng ý?",
            ],
            "red_flags": [
                "Không thể nêu ví dụ về lắng nghe người khác",
                "Luôn muốn kiểm soát mọi thứ",
            ],
        },
        "I": {
            "focus": [
                "Kiểm tra tính kiên trì và hoàn thành công việc chi tiết",
                "Đánh giá khả năng làm việc độc lập",
            ],
            "questions": [
                "Mô tả một dự án yêu cầu bạn làm việc một mình trong thời gian dài. "
                "Bạn duy trì động lực như thế nào?",
                "Khi phải xử lý một công việc nhiều chi tiết và số liệu, bạn tiếp cận ra sao?",
                "Kể về lần bạn phải hoàn thành một nhiệm vụ nhàm chán nhưng quan trọng.",
            ],
            "red_flags": [
                "Không có ví dụ cụ thể về hoàn thành công việc chi tiết",
                "Né tránh câu hỏi về kỷ luật",
            ],
        },
        "S": {
            "focus": [
                "Kiểm tra khả năng ra quyết định dưới áp lực",
                "Đánh giá tính chủ động và sáng tạo",
            ],
            "questions": [
                "Kể về lần bạn phải đưa ra quyết định nhanh mà không có đủ thông tin. "
                "Kết quả ra sao?",
                "Bạn xử lý thế nào khi đồng nghiệp không hoàn thành phần việc của họ?",
                "Mô tả lần gần nhất bạn chủ động đề xuất thay đổi tại nơi làm việc.",
            ],
            "red_flags": ["Luôn chờ chỉ đạo, không chủ động", "Tránh mâu thuẫn bằng mọi giá"],
        },
        "C": {
            "focus": [
                "Kiểm tra khả năng giao tiếp và linh hoạt",
                "Đánh giá cách xử lý khi không có đủ dữ liệu",
            ],
            "questions": [
                "Khi phải thuyết trình một chủ đề phức tạp cho người không chuyên, "
                "bạn làm thế nào?",
                "Kể về lần bạn phải quyết định khi dữ liệu không đầy đủ. Bạn xử lý ra sao?",
                "Bạn phản ứng thế nào khi team muốn tiến hành nhanh mà bạn chưa kiểm tra xong?",
            ],
            "red_flags": [
                "Quá cứng nhắc, không linh hoạt",
                "Không thể ra quyết định khi thiếu dữ liệu",
            ],
        },
    }

    if primary in disc_questions_map:
        data = disc_questions_map[primary]
        suggestions["focus_areas"] = data["focus"]
        suggestions["suggested_questions"] = data["questions"]
        suggestions["red_flags_to_watch"] = data["red_flags"]

    # Personality-based suggestions
    weak_areas = sorted(personality_scores.items(), key=lambda x: x[1])[:3]
    personality_questions = {
        "integrity": "Kể về tình huống bạn phải chọn giữa lợi ích cá nhân và sự trung thực. "
        "Bạn đã chọn gì?",
        "academic": "Chia sẻ về nghiên cứu hoặc phương pháp học tập bạn đang theo đuổi hiện tại.",
        "teamwork": "Mô tả cách bạn xử lý khi một thành viên nhóm không hợp tác.",
        "service": "Kể về lần bạn phải hỗ trợ ai đó ngoài phạm vi trách nhiệm của mình.",
        "discipline": "Bạn quản lý thời gian và deadline như thế nào khi có nhiều công việc "
        "cùng lúc?",
        "adaptability": "Kể về lần bạn phải thay đổi phương pháp làm việc giữa chừng. "
        "Kết quả ra sao?",
        "leadership": "Mô tả tình huống bạn phải đưa team đi đúng hướng khi mọi thứ đang "
        "hỗn loạn.",
        "responsibility": "Khi một dự án thất bại, bạn phản ứng và xử lý hậu quả như thế nào?",
        "stress": "Kể về giai đoạn áp lực nhất trong sự nghiệp. Bạn vượt qua bằng cách nào?",
    }

    for key, _score in weak_areas:
        if key in personality_questions:
            suggestions["suggested_questions"].append(personality_questions[key])

    suggestions["behavioral_patterns"] = [
        f"Profile DISC {profile}: {DISC_DESCRIPTIONS[primary]['traits'][0]} là đặc trưng chính",
        f"Điểm mạnh nổi bật: {', '.join(DISC_DESCRIPTIONS[primary]['strengths'][:2])}",
        f"Rủi ro cần theo dõi: {', '.join(DISC_DESCRIPTIONS[primary]['risks'][:2])}",
    ]

    return suggestions


def get_public_questions() -> dict[str, Any]:
    """Câu hỏi cho ứng viên làm bài — KHÔNG kèm đáp án mapping D/I/S/C.

    (Cải tiến bảo mật so với hệ cũ: hệ cũ nhúng cả key 'd' vào HTML,
    ứng viên xem source là biết cách "gian lận". Chấm điểm luôn ở server.)
    """
    return {
        "disc_questions": [
            {"options": [{"t": opt["t"]} for opt in q["options"]]} for q in DISC_QUESTIONS
        ],
        "personality_categories": [
            {"name": c["name"], "icon": c["icon"], "key": c["key"], "qs": c["qs"]}
            for c in PERSONALITY_CATEGORIES
        ],
    }
