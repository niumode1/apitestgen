"""Schema Validation Agent — validates response structure against OpenAPI schema."""

from typing import Any

from app.services.llm.agents.base import BaseAgent
from app.services.llm.provider import BaseLLMProvider


class SchemaValidationAgent(BaseAgent):
    """Generates tests that validate response body against the OpenAPI response schema."""

    def __init__(self, provider: BaseLLMProvider):
        super().__init__(
            provider=provider,
            prompt_template_name="schema_v.j2",
            system_prompt_name="code_system.j2",
        )

    async def generate(
        self,
        endpoint: dict[str, Any],
        analysis: dict[str, Any] | None = None,
        count: int = 3,
    ) -> tuple[str, int, int]:
        return await self.run({
            "endpoint": endpoint,
            "analysis": analysis or {},
            "count": count,
        })
