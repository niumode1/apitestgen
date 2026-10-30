"""Boundary Value Agent — generates edge-case tests at parameter boundaries."""

from typing import Any

from app.services.llm.agents.base import BaseAgent
from app.services.llm.provider import BaseLLMProvider


class BoundaryValueAgent(BaseAgent):
    """Generates boundary value tests: min, max, off-by-one, zero, null, empty."""

    def __init__(self, provider: BaseLLMProvider):
        super().__init__(
            provider=provider,
            prompt_template_name="boundary.j2",
            system_prompt_name="code_system.j2",
        )

    async def generate(
        self,
        endpoint: dict[str, Any],
        analysis: dict[str, Any] | None = None,
        count: int = 4,
    ) -> tuple[str, int, int]:
        return await self.run({
            "endpoint": endpoint,
            "analysis": analysis or {},
            "count": count,
        })
