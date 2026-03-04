"""Ollama local LLM provider — highest priority."""

import time
import requests
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class OllamaProvider(LLMProvider):
    PROVIDER_NAME = "ollama"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "codellama:7b", **kwargs):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._session: Optional[requests.Session] = None
        self._models_cache: Optional[List[str]] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 4096),
            },
        }
        try:
            resp = self._get_session().post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=kwargs.get("timeout", 180),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Ollama API error: {exc}") from exc

        return LLMResponse(
            content=data["message"]["content"],
            provider=self.PROVIDER_NAME,
            model=self.model,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=0.0,
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["base_url"] = self.base_url
        return info

    @property
    def available_models(self) -> List[str]:
        if self._models_cache is None:
            try:
                resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
                self._models_cache = [m["name"] for m in resp.json().get("models", [])]
            except Exception:
                self._models_cache = []
        return self._models_cache

    def generate_stream(self, messages: List[Message], **kwargs):
        """Generate a streaming response from Ollama."""
        import json
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 4096),
            },
        }
        
        try:
            with self._get_session().post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=kwargs.get("timeout", 180),
                stream=True,
            ) as resp:
                resp.raise_for_status()
                
                for line in resp.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
        except requests.RequestException as exc:
            raise ProviderError(f"Ollama streaming error: {exc}") from exc
