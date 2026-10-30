"""API Endpoint schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EndpointResponse(BaseModel):
    """Full endpoint detail."""
    id: str
    spec_id: str
    path: str
    method: str
    summary: str
    description: str
    operation_id: str
    tags: list[str]
    parameters: list[dict[str, Any]]
    request_body: Optional[dict[str, Any]] = None
    responses: dict[str, Any]
    security: Optional[list[dict[str, Any]]] = None
    deprecated: bool
    analyzed_at: Optional[datetime] = None
    analysis: Optional[dict[str, Any]] = None
    testcase_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EndpointBrief(BaseModel):
    """Brief endpoint for list view."""
    id: str
    path: str
    method: str
    summary: str
    tags: list[str]
    deprecated: bool
    analyzed_at: Optional[datetime] = None
    testcase_count: int = 0

    model_config = {"from_attributes": True}


class EndpointFilter(BaseModel):
    """Filter options for endpoint listing."""
    method: Optional[str] = None
    tag: Optional[str] = None
    search: Optional[str] = Field(default=None, description="Search in path, summary, operation_id")
    deprecated: Optional[bool] = None


class EndpointSummary(BaseModel):
    """Aggregated summary of endpoints in a spec."""
    total: int = 0
    by_method: dict[str, int] = Field(default_factory=dict)
    by_tag: dict[str, int] = Field(default_factory=dict)
    deprecated_count: int = 0
