import enum

from sqlalchemy import Enum as SAEnum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_id


class AssetType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    INFOGRAPHIC = "infographic"


class ApprovedAsset(TimestampMixin, Base):
    __tablename__ = "approved_assets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(SAEnum(AssetType, values_callable=lambda e: [x.value for x in e]), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
