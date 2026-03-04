"""Groq — Fastest inference, free tier available."""

import os
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "groq"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True

    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]

    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile", **kwargs):
        api_key = api_key or os.environ.get("GROQ_API_KEY")
        super().__init__(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key,
            model=model,
            timeout=60,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS

    def estimate_cost(self, tokens: int) -> float:
        return 0.0
