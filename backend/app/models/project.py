import enum

from sqlalchemy import Enum as SAEnum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_id


class ContentType(str, enum.Enum):
    EMAIL = "email"
    BANNER_AD = "banner_ad"
    SOCIAL_POST = "social_post"
    WEBSITE = "website"
    BROCHURE = "brochure"


class Audience(str, enum.Enum):
    HCP = "hcp"
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    PAYER = "payer"


class Goal(str, enum.Enum):
    AWARENESS = "awareness"
    EDUCATION = "education"
    CONVERSION = "conversion"
    RETENTION = "retention"


class Tone(str, enum.Enum):
    PROFESSIONAL = "professional"
    EMPATHETIC = "empathetic"
    URGENT = "urgent"
    OPTIMISTIC = "optimistic"


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    EXPORTED = "exported"


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    audience: Mapped[Audience] = mapped_column(SAEnum(Audience, values_callable=lambda e: [x.value for x in e]), nullable=False)
    goal: Mapped[Goal] = mapped_column(SAEnum(Goal, values_callable=lambda e: [x.value for x in e]), nullable=False)
    tone: Mapped[Tone] = mapped_column(SAEnum(Tone, values_callable=lambda e: [x.value for x in e]), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, values_callable=lambda e: [x.value for x in e]), nullable=False, default=ProjectStatus.DRAFT
    )
    brief_responses: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
