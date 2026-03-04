"""Azure OpenAI provider."""

import os
import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class AzureOpenAIProvider(LLMProvider):
    PROVIDER_NAME = "azure_openai"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True

    def __init__(self, api_key: str = None, endpoint: str = None,
                 deployment: str = "gpt-4", api_version: str = "2024-02-15-preview",
                 **kwargs):
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.endpoint = (endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT", "")).rstrip("/")
        self.deployment = deployment
        self.api_version = api_version
        self.model = deployment
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "api-key": self.api_key or "",
                "Content-Type": "application/json",
            })
        return self._session

    def is_available(self) -> bool:
        return bool(self.api_key and self.endpoint)

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        url = (
            f"{self.endpoint}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )
        body = {
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        try:
            resp = self._get_session().post(url, json=body, timeout=kwargs.get("timeout", 120))
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Azure OpenAI API error: {exc}") from exc

        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens")
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider=self.PROVIDER_NAME,
            model=self.deployment,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["endpoint"] = self.endpoint
        info["deployment"] = self.deployment
        return info
