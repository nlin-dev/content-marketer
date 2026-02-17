import enum

from sqlalchemy import Enum as SAEnum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_id


class ComplianceStatus(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class ComplianceRecord(TimestampMixin, Base):
    __tablename__ = "compliance_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    content_version_id: Mapped[str] = mapped_column(
        String, ForeignKey("content_versions.id"), nullable=False
    )
    check_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ComplianceStatus] = mapped_column(
        SAEnum(ComplianceStatus), nullable=False
    )
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
