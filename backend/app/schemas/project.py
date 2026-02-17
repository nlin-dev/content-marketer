from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import OrmModel

from app.models.project import Audience, ContentType, Goal, ProjectStatus, Tone
from app.schemas.user import UserResponse


class ProjectCreate(BaseModel):
    name: str = Field(max_length=255)
    content_type: ContentType
    audience: Audience
    goal: Goal
    tone: Tone


class ProjectBriefUpdate(BaseModel):
    brief_responses: dict


class ProjectResponse(OrmModel):
    id: str
    name: str
    content_type: ContentType
    audience: Audience
    goal: Goal
    tone: Tone
    status: ProjectStatus
    brief_responses: dict | None
    user_id: str
    user: UserResponse | None = None
    created_at: datetime
    updated_at: datetime
