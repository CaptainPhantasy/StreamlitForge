"""Replicate provider."""

import os
import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class ReplicateProvider(LLMProvider):
    PROVIDER_NAME = "replicate"
    SUPPORTS_STREAMING = True

    def __init__(self, api_key: str = None,
                 model: str = "meta/llama-2-70b-chat", **kwargs):
        self.api_key = api_key or os.environ.get("REPLICATE_API_KEY")
        self.model = model
        self.base_url = "https://api.replicate.com/v1"
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
        prompt = "\n".join(
            f"{m.role.value}: {m.content}" for m in messages
        )
        body = {
            "input": {
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "temperature": kwargs.get("temperature", 0.7),
            },
        }
        try:
            resp = self._get_session().post(
                f"{self.base_url}/models/{self.model}/predictions",
                json=body,
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Replicate API error: {exc}") from exc

        output = data.get("output", "")
        if isinstance(output, list):
            output = "".join(output)

        return LLMResponse(
            content=output,
            provider=self.PROVIDER_NAME,
            model=self.model,
            latency_ms=int((time.time() - start) * 1000),
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.base_url
        return info

    @property
    def available_models(self) -> List[str]:
        return [self.model]
