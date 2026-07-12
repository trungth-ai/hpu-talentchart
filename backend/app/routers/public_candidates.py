# Candidate portal — ứng viên đăng nhập Google (bất kỳ domain) để theo dõi hồ sơ (ADR-004)
# Token type=candidate tách biệt hoàn toàn khỏi token staff.

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success
from app.core.security import create_candidate_token, decode_token
from app.core.tenant_context import get_current_org_id
from app.database import get_db
from app.exceptions import ResourceNotFound, UnauthorizedError
from app.middleware.rate_limit import limiter
from app.models.candidate import Candidate
from app.models.test_session import TestSession
from app.schemas.auth import GoogleLoginRequest
from app.services import google_auth

router = APIRouter(prefix="/public", tags=["public"])

CANDIDATE_LOGIN_RATE_LIMIT = "10/minute"


async def get_current_candidate(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Candidate:
    """Dependency: xác thực token type=candidate (AuthMiddleware chỉ decode type=access)."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise UnauthorizedError()
    payload = decode_token(auth_header[7:].strip(), expected_type="candidate")

    org_id = get_current_org_id()
    token_org = UUID(payload["organization_id"])
    # Subdomain (nếu có) phải khớp org trong token — chặn dùng token chéo tenant
    if org_id is not None and org_id != token_org:
        raise UnauthorizedError()

    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == UUID(payload["sub"]))
        .where(Candidate.organization_id == token_org)
        .where(Candidate.status == "active")
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise UnauthorizedError()
    return candidate


@router.post("/auth/google")
@limiter.limit(CANDIDATE_LOGIN_RATE_LIMIT)
async def candidate_google_login(
    request: Request, data: GoogleLoginRequest, db: AsyncSession = Depends(get_db)
):
    """Ứng viên đăng nhập bằng Google (mọi domain, email đã verify).

    Find-or-create candidate theo email trong tenant hiện tại (theo subdomain).
    """
    org_id = get_current_org_id()
    if org_id is None:
        raise ResourceNotFound("trang tuyển dụng")

    claims = await google_auth.verify_google_id_token(data.id_token)
    email = claims["email"].lower()

    result = await db.execute(
        select(Candidate)
        .where(Candidate.email == email)
        .where(Candidate.organization_id == org_id)
        .where(Candidate.status == "active")
        .order_by(Candidate.created_at.desc())
        .limit(1)
    )
    candidate = result.scalar_one_or_none()

    if candidate is None:
        candidate = Candidate(
            full_name=claims.get("name") or email.split("@")[0],
            email=email,
            candidate_type="applicant",
            pipeline_stage="RECEIVED",
            source="google_login",
            # organization_id tự gán từ tenant context (before_flush listener)
        )
        db.add(candidate)
        await db.flush()
        await db.refresh(candidate)

    return success(
        {
            "candidate_token": create_candidate_token(candidate),
            "candidate": {
                "id": str(candidate.id),
                "full_name": candidate.full_name,
                "email": candidate.email,
                "pipeline_stage": candidate.pipeline_stage,
            },
        },
        message="Đăng nhập thành công",
    )


@router.get("/candidates/me")
async def candidate_me(candidate: Candidate = Depends(get_current_candidate)):
    """Ứng viên xem trạng thái hồ sơ của chính mình."""
    return success(
        {
            "id": str(candidate.id),
            "full_name": candidate.full_name,
            "email": candidate.email,
            "position": candidate.position,
            "pipeline_stage": candidate.pipeline_stage,
            "epa_consent": candidate.epa_consent,
        }
    )


@router.get("/candidates/me/test")
async def candidate_active_test(
    candidate: Candidate = Depends(get_current_candidate),
    db: AsyncSession = Depends(get_db),
):
    """Link bài test đang mở của ứng viên (nếu HR đã gửi)."""
    result = await db.execute(
        select(TestSession)
        .where(TestSession.candidate_id == candidate.id)
        .where(TestSession.is_used.is_(False))
        .where(TestSession.status == "active")
        .where(TestSession.expires_at > datetime.now(UTC))
        .order_by(TestSession.created_at.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ResourceNotFound("bài test đang mở")
    return success(
        {"token": session.token, "expires_at": session.expires_at.isoformat()}
    )
