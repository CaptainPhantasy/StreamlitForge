"""Shared utilities for OpenAI-compatible providers."""

import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class OpenAICompatibleProvider(LLMProvider):
    """Base class for providers using the OpenAI chat completions API format."""

    PROVIDER_NAME: str = "openai_compatible"
    SUPPORTS_STREAMING: bool = True

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        model: str = "default",
        timeout: float = 120.0,
        extra_headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.extra_headers = extra_headers or {}
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            headers: Dict[str, str] = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            headers.update(self.extra_headers)
            self._session.headers.update(headers)
        return self._session

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        try:
            resp = self._get_session().post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=kwargs.get("timeout", self.timeout),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"{self.PROVIDER_NAME} API error: {exc}") from exc

        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens")

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider=self.PROVIDER_NAME,
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=self.estimate_cost(tokens_used or 0),
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.base_url
        return info

    def generate_stream(self, messages: List[Message], **kwargs):
        """Generate a streaming response using SSE."""
        import json
        
        payload: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True,
        }
        
        try:
            session = self._get_session()
            with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=kwargs.get("timeout", self.timeout),
                stream=True,
            ) as resp:
                resp.raise_for_status()
                
                for line in resp.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                                
        except requests.RequestException as exc:
            raise ProviderError(f"{self.PROVIDER_NAME} streaming error: {exc}") from exc
