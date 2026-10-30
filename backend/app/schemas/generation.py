"""Test generation request/response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerationStrategy(str):
    ALL = "all"
    POSITIVE_ONLY = "positive_only"
    NEGATIVE_ONLY = "negative_only"
    BOUNDARY_ONLY = "boundary_only"
    SECURITY_ONLY = "security_only"
    SCHEMA_ONLY = "schema_only"


class GenerationRequest(BaseModel):
    """Request to start test generation."""
    spec_id: UUID
    endpoint_ids: Optional[list[UUID]] = Field(
        default=None, description="Specific endpoints to generate for; None = all"
    )
    strategy: str = Field(
        default=GenerationStrategy.ALL,
        pattern="^(all|positive_only|negative_only|boundary_only|security_only|schema_only)$",
    )
    llm_provider_id: Optional[UUID] = Field(default=None, description="Provider to use; None = default")
    max_testcases_per_endpoint: int = Field(default=10, ge=1, le=50)
    review_enabled: bool = True


class GenerationProgress(BaseModel):
    """Progress update during generation."""
    generation_id: str
    status: str  # analyzing, generating_positive, generating_negative, etc.
    endpoint_current: str = ""
    endpoint_index: int = 0
    endpoint_total: int = 0
    tests_generated: int = 0
    message: Optional[str] = None


class GenerationResponse(BaseModel):
    """Response after generation completes."""
    generation_id: str
    spec_id: str
    status: str
    endpoints_processed: int = 0
    total_testcases_generated: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    errors: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
