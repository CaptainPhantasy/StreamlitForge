"""Mistral AI provider."""

import os
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class MistralProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "mistral"
    SUPPORTS_STREAMING = True

    AVAILABLE_MODELS = [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
        "codestral-latest",
    ]

    def __init__(self, api_key: str = None, model: str = "mistral-large-latest", **kwargs):
        api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        super().__init__(
            base_url="https://api.mistral.ai/v1",
            api_key=api_key,
            model=model,
            timeout=60,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
