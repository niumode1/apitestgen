"""Project schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Request to create a project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    base_url: str = Field(default="", max_length=1024)


class ProjectUpdate(BaseModel):
    """Request to update a project."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    base_url: Optional[str] = Field(default=None, max_length=1024)


class ProjectResponse(BaseModel):
    """Project in API responses."""
    id: str
    name: str
    description: str
    base_url: str
    spec_count: int = 0
    testcase_count: int = 0
    execution_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectBrief(BaseModel):
    """Minimal project reference."""
    id: str
    name: str

    model_config = {"from_attributes": True}
