"""Defect Report schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""
    format: str = Field(default="markdown", pattern="^(markdown|html|pdf)$")
    include_llm_summary: bool = Field(
        default=True, description="Use LLM to write an executive summary"
    )


class ReportResponse(BaseModel):
    """Full report detail."""
    id: str
    execution_id: str
    project_id: str
    title: str
    summary: str
    format: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    failed_count: int
    error_count: int
    total_count: int
    pass_rate: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportBrief(BaseModel):
    """Brief report for list view."""
    id: str
    title: str
    format: str
    failed_count: int
    error_count: int
    total_count: int
    pass_rate: float
    created_at: datetime

    model_config = {"from_attributes": True}
