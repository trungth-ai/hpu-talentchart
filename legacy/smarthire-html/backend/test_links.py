from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID
import secrets

from app.database import get_db
from app.models import User, Candidate, TestLink, CandidateStatus
from app.schemas import TestLinkCreate, TestLinkResponse
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/test-links", tags=["Test Links"])

@router.post("/", response_model=TestLinkResponse)
async def create_test_link(
    data: TestLinkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if candidate with this email already completed test
    existing = await db.execute(
        select(Candidate).where(
            Candidate.email == data.email,
            Candidate.disc_scores.isnot(None)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email này đã hoàn thành bài test")
    
    # Check for existing unused link
    existing_link = await db.execute(
        select(TestLink).where(
            TestLink.email == data.email,
            TestLink.is_used == False,
            TestLink.expires_at > datetime.now(timezone.utc)
        )
    )
    if existing_link.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Đã có link test chưa sử dụng cho email này")
    
    # Create or find candidate
    cand_result = await db.execute(
        select(Candidate).where(Candidate.email == data.email)
    )
    candidate = cand_result.scalar_one_or_none()
    if not candidate:
        candidate = Candidate(
            full_name=data.full_name,
            email=data.email,
            position=data.position,
            campaign_id=data.campaign_id,
            status=CandidateStatus.TEST_SENT,
        )
        db.add(candidate)
        await db.flush()
    else:
        candidate.status = CandidateStatus.TEST_SENT
    
    # Create token
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.TEST_TOKEN_EXPIRE_HOURS)
    
    test_link = TestLink(
        token=token,
        candidate_id=candidate.id,
        campaign_id=data.campaign_id,
        email=data.email,
        expires_at=expires,
    )
    db.add(test_link)
    await db.commit()
    await db.refresh(test_link)
    
    resp = TestLinkResponse.model_validate(test_link)
    resp.test_url = f"{settings.BASE_URL}/test/{token}"
    return resp

@router.get("/", response_model=List[TestLinkResponse])
async def list_test_links(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TestLink).order_by(TestLink.created_at.desc()).limit(50)
    )
    links = result.scalars().all()
    responses = []
    for link in links:
        resp = TestLinkResponse.model_validate(link)
        resp.test_url = f"{settings.BASE_URL}/test/{link.token}"
        responses.append(resp)
    return responses

@router.get("/verify/{token}")
async def verify_test_link(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TestLink).where(TestLink.token == token)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link test không tồn tại")
    if link.is_used:
        raise HTTPException(status_code=400, detail="Link test đã được sử dụng")
    if link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Link test đã hết hạn")
    
    # Get candidate info
    cand = await db.execute(select(Candidate).where(Candidate.id == link.candidate_id))
    candidate = cand.scalar_one_or_none()
    
    return {
        "valid": True,
        "email": link.email,
        "candidate_name": candidate.full_name if candidate else "",
        "position": candidate.position if candidate else "",
        "expires_at": link.expires_at.isoformat(),
    }
