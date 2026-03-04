"""Anthropic Claude provider."""

import os
import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class AnthropicProvider(LLMProvider):
    PROVIDER_NAME = "anthropic"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True

    MODEL_PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, api_key: str = None, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        self.model = model
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "x-api-key": self.api_key or "",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            })
        return self._session

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()

        anthropic_messages = []
        system_prompt = None
        for m in messages:
            if m.role.value == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({"role": m.role.value, "content": m.content})

        body: Dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if system_prompt:
            body["system"] = system_prompt

        try:
            resp = self._get_session().post(
                f"{self.base_url}/messages",
                json=body,
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Anthropic API error: {exc}") from exc

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        return LLMResponse(
            content=content,
            provider=self.PROVIDER_NAME,
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=self.estimate_cost(tokens_used),
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.base_url
        return info

    def estimate_cost(self, tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model, {"input": 3.0, "output": 15.0})
        return (tokens * 0.7 * pricing["input"] + tokens * 0.3 * pricing["output"]) / 1_000_000

    @property
    def available_models(self) -> List[str]:
        return list(self.MODEL_PRICING.keys())
