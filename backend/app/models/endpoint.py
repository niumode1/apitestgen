"""API Endpoint model — one row per path+method combination."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.spec import OpenAPISpec
    from app.models.testcase import TestCase


class HTTPMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"


class APIEndpoint(Base, UUIDMixin, TimestampMixin):
    """A single API endpoint extracted from an OpenAPI spec."""

    __tablename__ = "endpoints"

    spec_id: Mapped[str] = mapped_column(
        ForeignKey("specs.id", ondelete="CASCADE"), nullable=False
    )

    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    method: Mapped[HTTPMethod] = mapped_column(
        Enum(HTTPMethod, name="http_method_enum"), nullable=False
    )
    summary: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    operation_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    parameters: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    request_body: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    responses: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    security: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Relationships
    spec: Mapped["OpenAPISpec"] = relationship("OpenAPISpec", back_populates="endpoints")
    testcases: Mapped[List["TestCase"]] = relationship(
        "TestCase", back_populates="endpoint", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<APIEndpoint {self.method.value} {self.path}>"
