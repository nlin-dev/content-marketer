import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, generate_id


class EventType(str, enum.Enum):
    PROJECT_CREATED = "project_created"
    VERSION_CREATED = "version_created"
    CONTENT_GENERATED = "content_generated"
    CONTENT_EDITED = "content_edited"
    COMPLIANCE_RUN = "compliance_run"
    COMMENT_ADDED = "comment_added"
    EXPORTED = "exported"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, values_callable=lambda e: [x.value for x in e]), nullable=False)
    user_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("projects.id"), nullable=True
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
