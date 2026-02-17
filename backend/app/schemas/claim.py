from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import OrmModel

from app.models.claim import ClaimCategory


class ClaimSourceResponse(OrmModel):
    source_id: str


class ClaimResponse(OrmModel):
    id: str
    text: str
    category: ClaimCategory
    sources: list[ClaimSourceResponse]
    is_active: bool
    created_at: datetime


class ClaimSearchResult(BaseModel):
    claim: ClaimResponse
    distance: float
