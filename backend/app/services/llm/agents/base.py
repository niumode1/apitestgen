"""Base agent class — all specialized agents extend this."""

import json
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

from jinja2 import Environment, FileSystemLoader, Template

from app.services.llm.provider import BaseLLMProvider, LLMResponse
from app.services.llm.token_counter import estimate_tokens
from app.utils.logger import logger


# Jinja2 environment for prompt templates
_templates_dir = Path(__file__).parent.parent / "prompts"
_jinja_env = Environment(loader=FileSystemLoader(str(_templates_dir)), autoescape=False)


def load_prompt(template_name: str) -> Template:
    """Load a Jinja2 prompt template by name (e.g., 'analyzer.j2')."""
    return _jinja_env.get_template(template_name)


def load_system_prompt(name: str = "default_system.j2") -> str:
    """Load a system prompt template and render it (no variables)."""
    template = _jinja_env.get_template(f"system/{name}")
    return template.render()


class BaseAgent:
    """Base class for all LLM agents.

    Each agent has:
    - A provider (OpenAI/Anthropic/Compatible)
    - A prompt template (Jinja2)
    - A run() method that renders the template, calls the LLM, returns output
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        prompt_template_name: str,
        system_prompt_name: str = "default_system.j2",
    ):
        self.provider = provider
        self.prompt_template = load_prompt(prompt_template_name)
        self.system_prompt = load_system_prompt(system_prompt_name)

    async def run(self, context: dict[str, Any]) -> tuple[str, int, int]:
        """Execute the agent: render prompt → call LLM → return (content, prompt_tokens, completion_tokens)."""
        user_prompt = self.prompt_template.render(**context)
        prompt_tokens_est = estimate_tokens(self.system_prompt + user_prompt, self.provider.model)

        logger.debug(
            f"Agent [{self.__class__.__name__}] sending ~{prompt_tokens_est} prompt tokens",
        )

        response: LLMResponse = await self.provider.complete(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=4096,
        )

        logger.debug(
            f"Agent [{self.__class__.__name__}] received {response.completion_tokens} completion tokens",
        )

        return response.content, response.prompt_tokens, response.completion_tokens

    async def run_streaming(self, context: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Execute agent with streaming output."""
        user_prompt = self.prompt_template.render(**context)

        async for token in self.provider.complete_stream(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=4096,
        ):
            yield token

    async def run_json(self, context: dict[str, Any]) -> tuple[dict[str, Any], int, int]:
        """Execute agent and parse output as JSON."""
        content, prompt_tokens, completion_tokens = await self.run(context)

        # Try to extract JSON from the response (handle markdown fences)
        json_str = content.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        try:
            parsed = json.loads(json_str)
            return parsed, prompt_tokens, completion_tokens
        except json.JSONDecodeError:
            # If parsing fails, try to find JSON object in the text
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                return parsed, prompt_tokens, completion_tokens
            logger.warning(f"Failed to parse JSON from agent output: {content[:200]}...")
            return {"raw": content}, prompt_tokens, completion_tokens
