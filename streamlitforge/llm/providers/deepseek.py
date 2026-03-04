"""DeepSeek provider — cost-effective, strong at code."""

import os
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "deepseek"
    SUPPORTS_STREAMING = True

    AVAILABLE_MODELS = ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]

    def __init__(self, api_key: str = None, model: str = "deepseek-chat", **kwargs):
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        super().__init__(
            base_url="https://api.deepseek.com/v1",
            api_key=api_key,
            model=model,
            timeout=120,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS

    def estimate_cost(self, tokens: int) -> float:
        return tokens * 0.0002 / 1000
