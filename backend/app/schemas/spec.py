"""OpenAPI Spec schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SpecParseStatus(str):
    PENDING = "pending"
    PARSED = "parsed"
    ERROR = "error"


class SpecResponse(BaseModel):
    """Spec in API responses."""
    id: str
    project_id: str
    name: str
    version: str
    spec_format: str
    parse_status: str
    parse_error: Optional[str] = None
    endpoint_count: int = 0
    imported_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SpecUploadResponse(BaseModel):
    """Response after uploading a spec."""
    id: str
    name: str
    version: str
    spec_format: str
    parse_status: str
    endpoint_count: int = 0
    message: str = ""


class SpecListResponse(BaseModel):
    """Brief spec info for list view."""
    id: str
    name: str
    version: str
    spec_format: str
    parse_status: str
    endpoint_count: int = 0
    imported_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
