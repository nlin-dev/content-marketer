from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import OrmModel


class CommentCreate(BaseModel):
    text: str
    anchor_selector: str | None = None
    parent_comment_id: str | None = None


class CommentResponse(OrmModel):
    id: str
    content_version_id: str
    user_id: str
    parent_comment_id: str | None
    text: str
    anchor_selector: str | None
    resolved: bool
    created_at: datetime
    updated_at: datetime


class CommentResolve(BaseModel):
    resolved: bool
