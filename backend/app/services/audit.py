from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, EventType


async def log(
    db: AsyncSession,
    event_type: EventType,
    user_id: str | None = None,
    project_id: str | None = None,
    payload: dict | None = None,
) -> None:
    entry = AuditLog(
        event_type=event_type,
        user_id=user_id,
        project_id=project_id,
        payload=payload,
    )
    db.add(entry)
    await db.flush()
