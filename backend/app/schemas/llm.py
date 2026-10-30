"""LLM Provider schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class LLMProviderCreate(BaseModel):
    """Request to add an LLM provider."""
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: str = Field(..., pattern="^(openai|anthropic|openai_compatible)$")
    api_base: str = Field(..., max_length=1024)
    api_key: Optional[str] = Field(default=None, description="Raw API key (encrypted at rest)")
    default_model: str = Field(..., min_length=1, max_length=100)
    extra_params: dict[str, Any] = Field(
        default_factory=lambda: {"temperature": 0.1, "max_tokens": 4096}
    )
    is_active: bool = True


class LLMProviderUpdate(BaseModel):
    """Request to update an LLM provider."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    provider_type: Optional[str] = Field(default=None, pattern="^(openai|anthropic|openai_compatible)$")
    api_base: Optional[str] = Field(default=None, max_length=1024)
    api_key: Optional[str] = Field(default=None, description="Raw API key (encrypted at rest)")
    default_model: Optional[str] = Field(default=None, min_length=1, max_length=100)
    extra_params: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class LLMProviderResponse(BaseModel):
    """Provider in API responses (api_key is never returned)."""
    id: str
    name: str
    provider_type: str
    api_base: str
    default_model: str
    extra_params: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LLMProviderTestRequest(BaseModel):
    """Request to test provider connectivity."""
    pass


class LLMProviderTestResponse(BaseModel):
    """Response from provider connectivity test."""
    success: bool
    message: str
    models: list[str] = Field(default_factory=list)
