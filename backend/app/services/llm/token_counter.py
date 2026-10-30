"""Token counting and cost estimation utilities.

Uses tiktoken for OpenAI models, with fallback estimation for others.
"""

import re
from typing import Optional


# Approximate tokens per character for models without tiktoken support
TOKENS_PER_CHAR_ESTIMATE = 0.25  # ~4 chars per token as rough estimate

# Pricing per 1M tokens (input / output) — update as needed
PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
    "claude-3.5-sonnet": (3.00, 15.00),
    "default": (0.15, 0.60),  # fallback
}


def estimate_tokens(text: str, model: Optional[str] = None) -> int:
    """Estimate token count for a text string.

    Uses tiktoken if available for OpenAI models, falls back to heuristic.
    """
    if not text:
        return 0

    # Try tiktoken
    try:
        import tiktoken
        if model and model.startswith("gpt-"):
            enc = tiktoken.encoding_for_model(model)
        else:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except (ImportError, KeyError):
        pass

    # Fallback: character-based estimate
    # Code-heavy text has more tokens per char; use a conservative estimate
    return max(1, int(len(text) * TOKENS_PER_CHAR_ESTIMATE))


def estimate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Estimate USD cost for an LLM call."""
    input_price, output_price = PRICING.get(model, PRICING["default"])
    cost = (prompt_tokens / 1_000_000) * input_price + (completion_tokens / 1_000_000) * output_price
    return round(cost, 6)


def count_pytest_tokens(code: str) -> dict:
    """Analyze a generated pytest function for token metrics."""
    lines = code.strip().split("\n")
    return {
        "lines": len(lines),
        "chars": len(code),
        "estimated_tokens": estimate_tokens(code),
        "has_assertions": "assert" in code,
        "has_async": "async def" in code,
        "function_count": len(re.findall(r"async def test_", code)),
    }
