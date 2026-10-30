"""LLM Provider abstraction layer.

Supports OpenAI, Anthropic, and OpenAI-compatible (Ollama, vLLM, etc.) backends.
All providers expose a uniform async interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Optional

from app.config import settings
from app.models.llm import LLMProvider as LLMProviderModel
from app.models.llm import ProviderType


@dataclass
class LLMResponse:
    """Uniform response from any LLM provider."""
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self, model: str, api_key: Optional[str] = None, api_base: str = "", **kwargs: Any):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.extra_kwargs = kwargs

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send a prompt and return the completion."""
        ...

    @abstractmethod
    async def complete_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion token by token."""
        ...

    async def test_connection(self) -> tuple[bool, str]:
        """Quick connectivity test."""
        try:
            response = await self.complete(
                system_prompt="You are a helpful assistant.",
                user_prompt="Reply with just 'OK'.",
                max_tokens=10,
            )
            return True, f"Connected. Model: {response.model}"
        except Exception as e:
            return False, str(e)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider (also works for any OpenAI-compatible endpoint)."""

    def __init__(self, model: str, api_key: Optional[str] = None, api_base: str = "", **kwargs: Any):
        super().__init__(model=model, api_key=api_key, api_base=api_base, **kwargs)
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=api_key or "not-needed",
            base_url=api_base or "https://api.openai.com/v1",
            timeout=settings.LLM_REQUEST_TIMEOUT,
        )

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            finish_reason=choice.finish_reason or "stop",
        )

    async def complete_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    def __init__(self, model: str, api_key: Optional[str] = None, api_base: str = "", **kwargs: Any):
        super().__init__(model=model, api_key=api_key, api_base=api_base, **kwargs)
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(
                api_key=api_key,
                timeout=settings.LLM_REQUEST_TIMEOUT,
            )
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install: pip install anthropic"
            )

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            finish_reason=response.stop_reason or "stop",
        )

    async def complete_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        import anthropic
        try:
            async with self.client.messages.stream(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.APIStatusError as e:
            raise RuntimeError(f"Anthropic API error: {e.message}") from e


class LLMProviderFactory:
    """Create the correct provider instance from a DB record or config."""

    @staticmethod
    def create_from_model(provider_record: LLMProviderModel) -> BaseLLMProvider:
        """Build a provider from a database record."""
        api_key = provider_record.api_key_encrypted  # TODO: decrypt in production

        extra = provider_record.extra_params or {}
        temperature = extra.pop("temperature", 0.1)
        max_tokens = extra.pop("max_tokens", 4096)

        if provider_record.provider_type == ProviderType.ANTHROPIC:
            return AnthropicProvider(
                model=provider_record.default_model,
                api_key=api_key,
                api_base=provider_record.api_base,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra,
            )
        else:
            # Both OPENAI and OPENAI_COMPATIBLE use the OpenAI client
            return OpenAIProvider(
                model=provider_record.default_model,
                api_key=api_key,
                api_base=provider_record.api_base,
                temperature=temperature,
                max_tokens=max_tokens,
                **extra,
            )

    @staticmethod
    def create_default() -> BaseLLMProvider:
        """Create a provider from environment config (fallback)."""
        if settings.DEFAULT_LLM_PROVIDER == "anthropic":
            return AnthropicProvider(
                model=settings.DEFAULT_MODEL,
                api_key=settings.ANTHROPIC_API_KEY,
            )
        else:
            return OpenAIProvider(
                model=settings.DEFAULT_MODEL,
                api_key=settings.OPENAI_API_KEY,
                api_base=settings.OPENAI_BASE_URL,
            )
