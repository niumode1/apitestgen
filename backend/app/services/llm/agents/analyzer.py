"""Endpoint Analyzer Agent — analyzes API endpoint semantics and constraints."""

from typing import Any

from app.services.llm.agents.base import BaseAgent, load_system_prompt
from app.services.llm.provider import BaseLLMProvider


class EndpointAnalyzerAgent(BaseAgent):
    """Analyzes an API endpoint to extract parameter semantics, constraints, risks, and test suggestions.

    Output is structured JSON consumed by downstream generators.
    """

    def __init__(self, provider: BaseLLMProvider):
        super().__init__(
            provider=provider,
            prompt_template_name="analyzer.j2",
            system_prompt_name="default_system.j2",
        )

    async def analyze(self, endpoint_context: dict[str, Any]) -> dict[str, Any]:
        """Run analysis and return structured JSON.

        Args:
            endpoint_context: Dict with endpoint fields (path, method, summary,
                              description, operation_id, tags, parameters,
                              request_body, responses)

        Returns:
            Parsed JSON analysis dict with parameter_insights, auth info, test priorities, edge_cases.
        """
        result, prompt_tokens, completion_tokens = await self.run_json(
            {"endpoint": endpoint_context}
        )
        result["_meta"] = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        return result
