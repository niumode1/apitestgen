"""Shared Pydantic schemas: pagination, error responses, filters."""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class ErrorDetail(BaseModel):
    """Validation error detail."""
    loc: list[str] = Field(default_factory=list)
    msg: str = ""
    type: str = ""


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = ""
    errors: list[ErrorDetail] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = ""
    environment: str = ""


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str = ""
