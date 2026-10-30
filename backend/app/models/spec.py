"""OpenAPI Spec model — stores imported API specifications."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.endpoint import APIEndpoint
    from app.models.project import Project


class SpecFormat(str, enum.Enum):
    JSON = "json"
    YAML = "yaml"


class ParseStatus(str, enum.Enum):
    PENDING = "pending"
    PARSED = "parsed"
    ERROR = "error"


class OpenAPISpec(Base, UUIDMixin, TimestampMixin):
    """An imported OpenAPI specification."""

    __tablename__ = "specs"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    spec_format: Mapped[SpecFormat] = mapped_column(
        Enum(SpecFormat, name="spec_format_enum"), default=SpecFormat.JSON, nullable=False
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    parse_status: Mapped[ParseStatus] = mapped_column(
        Enum(ParseStatus, name="parse_status_enum"),
        default=ParseStatus.PENDING,
        nullable=False,
    )
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="specs")
    endpoints: Mapped[List["APIEndpoint"]] = relationship(
        "APIEndpoint", back_populates="spec", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<OpenAPISpec id={self.id!r} name={self.name!r} v{self.version}>"
