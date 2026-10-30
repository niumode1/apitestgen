"""Postman Collection model."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.project import Project


class PostmanCollection(Base, UUIDMixin, TimestampMixin):
    """An imported Postman collection."""

    __tablename__ = "postman_collections"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    collection_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="postman_collections")

    def __repr__(self) -> str:
        return f"<PostmanCollection id={self.id!r} name={self.name!r}>"
