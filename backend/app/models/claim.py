import enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_id


class ClaimCategory(str, enum.Enum):
    EFFICACY_OS = "efficacy_os"
    EFFICACY_PFS = "efficacy_pfs"
    SAFETY = "safety"
    MOA = "moa"
    DOSING = "dosing"
    QOL = "qol"
    SUBGROUPS = "subgroups"
    DCR = "dcr"
    UNMET_NEED = "unmet_need"
    POSITIONING = "positioning"


claim_sources = Table(
    "claim_sources",
    Base.metadata,
    Column("claim_id", String, ForeignKey("claims.id"), primary_key=True),
    Column("source_id", String, primary_key=True),
)


class Claim(TimestampMixin, Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ClaimCategory] = mapped_column(
        SAEnum(ClaimCategory, values_callable=lambda e: [x.value for x in e]), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.5, server_default="0.5")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)


claim_embedding_idx = Index(
    "ix_claims_embedding_hnsw",
    Claim.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
