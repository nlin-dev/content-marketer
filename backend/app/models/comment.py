from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, generate_id


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_id)
    content_version_id: Mapped[str] = mapped_column(
        String, ForeignKey("content_versions.id"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False
    )
    parent_comment_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("comments.id"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    anchor_selector: Mapped[str | None] = mapped_column(String(500), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
