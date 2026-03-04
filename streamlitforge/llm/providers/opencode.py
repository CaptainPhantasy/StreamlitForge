"""OpenCode Go and OpenCode Zen providers."""

import os
import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError
from ._openai_compat import OpenAICompatibleProvider


class OpenCodeGoProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "opencode_go"
    SUPPORTS_STREAMING = True

    MODELS = ["glm-5", "kimi-k2.5", "minimax-m2.5"]
    DEFAULT_MODEL = "minimax-m2.5"

    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        api_key = api_key or os.environ.get("OPENCODE_API_KEY")
        super().__init__(
            base_url="https://opencode.ai/zen/go/v1",
            api_key=api_key,
            model=model or self.DEFAULT_MODEL,
            timeout=120,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def available_models(self) -> List[str]:
        return self.MODELS

    def estimate_cost(self, tokens: int) -> float:
        return 0.0


class OpenCodeZenProvider(LLMProvider):
    PROVIDER_NAME = "opencode_zen"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True

    BASE_URL_OPENAI = "https://opencode.ai/zen/v1"

    FREE_MODELS = ["minimax-m2.5-free", "big-pickle", "gpt-5-nano"]

    MODEL_PRICING = {
        "minimax-m2.5-free": {"input": 0.0, "output": 0.0},
        "big-pickle": {"input": 0.0, "output": 0.0},
        "gpt-5-nano": {"input": 0.0, "output": 0.0},
        "claude-opus-4-6": {"input": 5.0, "output": 25.0},
        "claude-sonnet-4-6": {"input": 1.5, "output": 7.5},
        "claude-haiku-4": {"input": 0.5, "output": 2.0},
        "gpt-5-turbo": {"input": 2.0, "output": 8.0},
        "gpt-5": {"input": 5.0, "output": 15.0},
        "gemini-3-pro": {"input": 1.5, "output": 6.0},
        "gemini-3-flash": {"input": 0.3, "output": 1.0},
        "qwen3-coder": {"input": 0.5, "output": 1.5},
        "deepseek-r1": {"input": 0.5, "output": 2.0},
    }

    ANTHROPIC_MODELS = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4"]

    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-6", **kwargs):
        self.api_key = api_key or os.environ.get("OPENCODE_API_KEY")
        self.model = model
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def is_available(self) -> bool:
        return bool(self.api_key)

    @property
    def _is_anthropic_model(self) -> bool:
        return any(m in self.model for m in self.ANTHROPIC_MODELS)

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        if self._is_anthropic_model:
            return self._generate_anthropic(messages, **kwargs)
        return self._generate_openai(messages, **kwargs)

    def _generate_openai(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        body = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        try:
            resp = self._get_session().post(
                f"{self.BASE_URL_OPENAI}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"OpenCode Zen API error: {exc}") from exc

        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider=self.PROVIDER_NAME,
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=self.estimate_cost(tokens_used),
        )

    def _generate_anthropic(self, messages: List[Message], **kwargs) -> LLMResponse:
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
                f"{self.BASE_URL_OPENAI}/messages",
                headers={
                    "x-api-key": self.api_key or "",
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=body,
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"OpenCode Zen API error: {exc}") from exc

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

    def estimate_cost(self, tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model, {"input": 1.0, "output": 3.0})
        return (tokens * 0.7 * pricing["input"] + tokens * 0.3 * pricing["output"]) / 1_000_000

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.BASE_URL_OPENAI
        info["is_anthropic_model"] = self._is_anthropic_model
        return info

    @property
    def available_models(self) -> List[str]:
        return list(self.MODEL_PRICING.keys())
