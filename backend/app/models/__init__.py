# Models package — import tất cả model để Alembic autogenerate và Base.metadata thấy đủ bảng
from app.models.astrology import AstrologyReference
from app.models.base import Base, TenantScopedBase
from app.models.campaign import Campaign
from app.models.candidate import Candidate
from app.models.fortune_content import FortuneContent
from app.models.job_post import JobPost
from app.models.organization import Organization
from app.models.test_session import TestSession
from app.models.user import User

__all__ = [
    "Base",
    "TenantScopedBase",
    "AstrologyReference",
    "FortuneContent",
    "Organization",
    "User",
    "Campaign",
    "Candidate",
    "JobPost",
    "TestSession",
]
