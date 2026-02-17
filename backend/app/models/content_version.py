from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, generate_id


content_version_claims = Table(
    "content_version_claims",
    Base.metadata,
    Column(
        "content_version_id",
        String,
        ForeignKey("content_versions.id"),
        primary_key=True,
    ),
    Column("claim_id", String, ForeignKey("claims.id"), primary_key=True),
)

content_version_assets = Table(
    "content_version_assets",
    Base.metadata,
    Column(
        "content_version_id",
        String,
        ForeignKey("content_versions.id"),
        primary_key=True,
    ),
    Column(
        "approved_asset_id",
        String,
        ForeignKey("approved_assets.id"),
        primary_key=True,
    ),
)


class ContentVersion(Base):
    __tablename__ = "content_versions"
    __table_args__ = (
        UniqueConstraint("project_id", "version_number", name="uq_project_version"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    project_id: Mapped[str] = mapped_column(
        String, ForeignKey("projects.id"), nullable=False
    )
    parent_version_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("content_versions.id"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
    edit_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
