"""OpenRouter — Unified API for 100+ models."""

import os
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "openrouter"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True

    MODEL_PRICING = {
        "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "openai/gpt-4o": {"input": 2.5, "output": 10.0},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
        "google/gemini-pro-1.5": {"input": 2.5, "output": 10.0},
        "meta-llama/llama-3.1-70b-instruct": {"input": 0.52, "output": 0.75},
        "mistralai/mistral-large": {"input": 2.0, "output": 6.0},
        "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    }

    def __init__(self, api_key: str = None, model: str = "openai/gpt-4o-mini", **kwargs):
        api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model,
            timeout=120,
            extra_headers={
                "HTTP-Referer": "https://streamlitforge.dev",
                "X-Title": "StreamlitForge",
            },
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return list(self.MODEL_PRICING.keys())

    def estimate_cost(self, tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model, {"input": 1.0, "output": 3.0})
        return (tokens * 0.7 * pricing["input"] + tokens * 0.3 * pricing["output"]) / 1_000_000
