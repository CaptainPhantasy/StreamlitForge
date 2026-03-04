"""Cohere provider."""

import os
import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class CohereProvider(LLMProvider):
    PROVIDER_NAME = "cohere"
    SUPPORTS_STREAMING = True

    AVAILABLE_MODELS = ["command-r-plus", "command-r", "command"]

    def __init__(self, api_key: str = None, model: str = "command-r-plus", **kwargs):
        self.api_key = api_key or os.environ.get("COHERE_API_KEY")
        self.model = model
        self.base_url = "https://api.cohere.ai/v2"
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key or ''}",
                "Content-Type": "application/json",
            })
        return self._session

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        body: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        try:
            resp = self._get_session().post(
                f"{self.base_url}/chat",
                json=body,
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Cohere API error: {exc}") from exc

        content = data.get("message", {}).get("content", [{}])
        text = content[0].get("text", "") if content else ""

        usage = data.get("usage", {}).get("tokens", {})
        tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        return LLMResponse(
            content=text,
            provider=self.PROVIDER_NAME,
            model=self.model,
            tokens_used=tokens_used or None,
            latency_ms=int((time.time() - start) * 1000),
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.base_url
        return info

    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
