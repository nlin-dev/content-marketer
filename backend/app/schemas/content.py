from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import OrmModel

from app.schemas.compliance import ComplianceCheckResponse


class GenerateRequest(BaseModel):
    claim_ids: list[str] = Field(min_length=1)
    asset_ids: list[str] = []


class EditRequest(BaseModel):
    instruction: str = Field(min_length=1)


class DirectEditRequest(BaseModel):
    html_content: str


class AssetSwapRequest(BaseModel):
    old_asset_id: str
    new_asset_id: str


class RevertRequest(BaseModel):
    target_version_id: str


class VersionSummary(OrmModel):
    id: str
    version_number: int
    edit_instruction: str | None
    created_at: datetime


class VersionResponse(OrmModel):
    id: str
    project_id: str
    parent_version_id: str | None
    version_number: int
    html_content: str
    edit_instruction: str | None
    created_at: datetime
    claim_ids: list[str]
    asset_ids: list[str]
    compliance_checks: list[ComplianceCheckResponse] = []


class GenerateResponse(BaseModel):
    version: VersionResponse


class EditResponse(BaseModel):
    version: VersionResponse


class ExportResponse(BaseModel):
    project_name: str
    html_content: str
    version_number: int
    compliance_status: str
    exported_at: datetime
