"""OpenAI provider."""

import os
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "openai"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True

    MODEL_PRICING = {
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "o1": {"input": 15.0, "output": 60.0},
        "o1-mini": {"input": 3.0, "output": 12.0},
    }

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", **kwargs):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        super().__init__(
            base_url="https://api.openai.com/v1",
            api_key=api_key,
            model=model,
            timeout=120,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return list(self.MODEL_PRICING.keys())

    def estimate_cost(self, tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model, {"input": 1.0, "output": 3.0})
        return (tokens * 0.7 * pricing["input"] + tokens * 0.3 * pricing["output"]) / 1_000_000
