from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import OrmModel

from app.models.compliance import ComplianceStatus


class ComplianceCheckResponse(OrmModel):
    id: str
    content_version_id: str
    check_name: str
    status: ComplianceStatus
    details: dict | None
    created_at: datetime


class ComplianceReportResponse(BaseModel):
    checks: list[ComplianceCheckResponse]
    overall_status: ComplianceStatus
