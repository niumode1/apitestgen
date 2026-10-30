"""Postman import/export schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PostmanImportResponse(BaseModel):
    """Response after importing a Postman collection."""
    project_id: str
    project_name: str
    collection_name: str
    endpoint_count: int
    message: str = ""


class PostmanExportRequest(BaseModel):
    """Request to export endpoints as a Postman collection."""
    spec_id: Optional[str] = Field(default=None, description="Export endpoints from specific spec")
    endpoint_ids: Optional[list[str]] = Field(default=None, description="Specific endpoints to export")
    include_testcases: bool = Field(
        default=True, description="Include test case data as example requests"
    )


class PostmanCollectionResponse(BaseModel):
    """Postman collection in API responses."""
    id: str
    project_id: str
    name: str
    item_count: int
    imported_at: datetime

    model_config = {"from_attributes": True}


class PostmanExportResponse(BaseModel):
    """The exported Postman collection JSON."""
    collection: dict[str, Any]
