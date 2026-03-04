"""Together AI provider."""

import os
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class TogetherProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "together"
    SUPPORTS_STREAMING = True

    AVAILABLE_MODELS = [
        "meta-llama/Llama-3-70b-chat-hf",
        "meta-llama/Llama-3-8b-chat-hf",
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
    ]

    def __init__(self, api_key: str = None,
                 model: str = "meta-llama/Llama-3-70b-chat-hf", **kwargs):
        api_key = api_key or os.environ.get("TOGETHER_API_KEY")
        super().__init__(
            base_url="https://api.together.xyz/v1",
            api_key=api_key,
            model=model,
            timeout=120,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
