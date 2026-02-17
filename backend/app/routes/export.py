from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ComplianceRecord, ComplianceStatus, ContentVersion, Project
from app.schemas import ExportResponse

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/{version_id}", response_model=ExportResponse)
async def export_content(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> ExportResponse:
    version = await db.get(ContentVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    compliance_result = await db.execute(
        select(ComplianceRecord).where(
            ComplianceRecord.content_version_id == version_id
        )
    )
    records = list(compliance_result.scalars().all())

    if not records or any(r.status != ComplianceStatus.PASS for r in records):
        raise HTTPException(
            status_code=400,
            detail="Content is not compliant. Please resolve compliance issues before exporting.",
        )

    project = await db.get(Project, version.project_id)

    return ExportResponse(
        project_name=project.name if project else "Unknown",
        html_content=version.html_content,
        version_number=version.version_number,
        compliance_status="pass",
        exported_at=datetime.now(timezone.utc),
    )
