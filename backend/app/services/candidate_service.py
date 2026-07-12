# Candidate service — state machine pipeline (Critical Business Rules, xem ADR-007)
#
# Quy tắc: đi TIẾN tuần tự NEW → SCREENING → TEST_SENT → TEST_DONE → INTERVIEW → DECISION,
# từ DECISION rẽ HIRED hoặc REJECTED. Riêng REJECTED được phép chuyển tới từ BẤT KỲ bước
# chưa kết thúc (từ chối sớm). Không nhảy cóc bước tiến, không đi lùi, không rời khỏi
# trạng thái kết thúc (HIRED/REJECTED).

from app.exceptions import BusinessRuleError
from app.models.candidate import PIPELINE_STAGES, TERMINAL_STAGES, Candidate

# Chuỗi tuần tự trước nhánh rẽ
_SEQUENTIAL = ("NEW", "SCREENING", "TEST_SENT", "TEST_DONE", "INTERVIEW", "DECISION")


def get_allowed_next_stages(current_stage: str) -> tuple[str, ...]:
    """Trả về các trạng thái được phép chuyển đến từ trạng thái hiện tại.

    Đi TIẾN đúng 1 bước kế; cho phép REJECTED (từ chối) từ mọi bước chưa kết thúc (ADR-007).
    """
    if current_stage in TERMINAL_STAGES:
        return ()
    if current_stage == "DECISION":
        return TERMINAL_STAGES  # HIRED hoặc REJECTED
    idx = _SEQUENTIAL.index(current_stage)
    return (_SEQUENTIAL[idx + 1], "REJECTED")  # bước kế HOẶC từ chối sớm


def transition_pipeline(candidate: Candidate, target_stage: str) -> None:
    """Chuyển trạng thái pipeline — raise BusinessRuleError nếu vi phạm tuần tự."""
    if target_stage not in PIPELINE_STAGES:
        raise BusinessRuleError(
            f"Trạng thái '{target_stage}' không hợp lệ "
            f"(chọn: {', '.join(PIPELINE_STAGES)})"
        )

    current = candidate.pipeline_stage
    allowed = get_allowed_next_stages(current)

    if not allowed:
        raise BusinessRuleError(
            f"Ứng viên đã ở trạng thái kết thúc '{current}', không thể chuyển tiếp"
        )
    if target_stage not in allowed:
        raise BusinessRuleError(
            f"Không thể chuyển từ '{current}' sang '{target_stage}' — "
            f"chỉ được đi tiến 1 bước hoặc Từ chối; hợp lệ: {' / '.join(allowed)}"
        )

    candidate.pipeline_stage = target_stage


def clear_epa_data(candidate: Candidate) -> None:
    """Xóa dữ liệu nhạy cảm EPA — phục vụ quyền xóa trong 30 ngày (NĐ 13/2023/NĐ-CP)."""
    candidate.epa_consent = False
    candidate.epa_consent_at = None
    candidate.birth_date = None
    candidate.birth_time = None
    candidate.birth_place = None
