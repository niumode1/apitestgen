"""Positive Test Case Agent — generates happy-path pytest test cases."""

from typing import Any

from app.services.llm.agents.base import BaseAgent
from app.services.llm.provider import BaseLLMProvider


class PositiveCaseAgent(BaseAgent):
    """Generates positive (happy-path) pytest test cases for an API endpoint."""

    def __init__(self, provider: BaseLLMProvider):
        super().__init__(
            provider=provider,
            prompt_template_name="positive.j2",
            system_prompt_name="code_system.j2",
        )

    async def generate(
        self,
        endpoint: dict[str, Any],
        analysis: dict[str, Any] | None = None,
        count: int = 3,
    ) -> tuple[str, int, int]:
        """Generate positive test cases.

        Args:
            endpoint: Dict with endpoint fields
            analysis: Optional prior analysis from EndpointAnalyzerAgent
            count: Number of test cases to generate (default 3)

        Returns:
            (code: str, prompt_tokens: int, completion_tokens: int)
        """
        return await self.run({
            "endpoint": endpoint,
            "analysis": analysis or {},
            "count": count,
        })
