"""LLM Provider model."""

import enum
from typing import Any, Optional

from sqlalchemy import Boolean, Enum, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ProviderType(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENAI_COMPATIBLE = "openai_compatible"


class LLMProvider(Base, UUIDMixin, TimestampMixin):
    """A configured LLM provider."""

    __tablename__ = "llm_providers"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    provider_type: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType, name="provider_type_enum"), nullable=False
    )
    api_base: Mapped[str] = mapped_column(String(1024), nullable=False)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    default_model: Mapped[str] = mapped_column(String(100), nullable=False)
    extra_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<LLMProvider id={self.id!r} name={self.name!r} type={self.provider_type.value}>"
