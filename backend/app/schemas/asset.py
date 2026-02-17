from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import OrmModel

from app.models.approved_asset import AssetType


class AssetResponse(OrmModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, serialize_by_alias=True)

    id: str
    name: str
    asset_type: AssetType
    file_url: str
    metadata_: dict | None = Field(None, alias="metadata")
    created_at: datetime
    updated_at: datetime


class AssetSearchResult(BaseModel):
    asset: AssetResponse
    relevance: float
