from datetime import datetime

from app.schemas.base import OrmModel

from app.models.audit_log import EventType


class AuditLogResponse(OrmModel):
    id: str
    event_type: EventType
    user_id: str | None
    project_id: str | None
    payload: dict | None
    created_at: datetime
