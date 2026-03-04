"""Google Gemini provider."""

import os
import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class GoogleProvider(LLMProvider):
    PROVIDER_NAME = "google"
    SUPPORTS_STREAMING = True
    SUPPORTS_VISION = True

    AVAILABLE_MODELS = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(self, api_key: str = None, model: str = "gemini-2.0-flash", **kwargs):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        contents = []
        system_instruction = None
        for m in messages:
            if m.role.value == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role.value == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        body: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.7),
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
            },
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        model_name = kwargs.get("model", self.model)
        url = f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key}"

        try:
            resp = self._get_session().post(url, json=body, timeout=kwargs.get("timeout", 120))
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Google API error: {exc}") from exc

        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            content = ""

        usage = data.get("usageMetadata", {})
        tokens_used = usage.get("totalTokenCount")

        return LLMResponse(
            content=content,
            provider=self.PROVIDER_NAME,
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=0.0,
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.base_url
        return info

    @property
    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS
