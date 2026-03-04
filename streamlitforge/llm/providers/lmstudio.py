"""LM Studio — OpenAI-compatible local server."""

import requests
from typing import List

from ._openai_compat import OpenAICompatibleProvider


class LMStudioProvider(OpenAICompatibleProvider):
    PROVIDER_NAME = "lmstudio"
    SUPPORTS_STREAMING = True

    def __init__(self, base_url: str = "http://localhost:1234/v1",
                 model: str = "local-model", **kwargs):
        super().__init__(base_url=base_url, model=model, timeout=180)

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    @property
    def available_models(self) -> List[str]:
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            return [m["id"] for m in resp.json().get("data", [])]
        except Exception:
            return []
