"""AWS Bedrock provider."""

import os
import time
import json
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from ..base import LLMProvider, LLMResponse, Message, ProviderError


class AWSBedrockProvider(LLMProvider):
    PROVIDER_NAME = "aws_bedrock"
    SUPPORTS_STREAMING = True

    def __init__(self, access_key: str = None, secret_key: str = None,
                 region: str = "us-east-1",
                 model: str = "anthropic.claude-3-sonnet-20240229-v1:0", **kwargs):
        self.access_key = access_key or os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.region = region
        self.model = model
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def is_available(self) -> bool:
        return bool(self.access_key and self.secret_key)

    def _sign_request(self, method: str, url: str, headers: dict, body: bytes) -> dict:
        """Create AWS Signature V4 headers (minimal implementation)."""
        now = datetime.now(timezone.utc)
        datestamp = now.strftime("%Y%m%d")
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        service = "bedrock"
        credential_scope = f"{datestamp}/{self.region}/{service}/aws4_request"

        from urllib.parse import urlparse
        parsed = urlparse(url)
        canonical_uri = parsed.path
        canonical_querystring = parsed.query

        headers_to_sign = {
            "host": parsed.hostname,
            "x-amz-date": amz_date,
            "content-type": "application/json",
        }
        signed_headers = ";".join(sorted(headers_to_sign.keys()))
        canonical_headers = "".join(f"{k}:{v}\n" for k, v in sorted(headers_to_sign.items()))
        payload_hash = hashlib.sha256(body).hexdigest()

        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        )

        def _sign(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()

        k_date = _sign(f"AWS4{self.secret_key}".encode(), datestamp)
        k_region = _sign(k_date, self.region)
        k_service = _sign(k_region, service)
        k_signing = _sign(k_service, "aws4_request")
        signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

        auth = (
            f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        return {
            "Authorization": auth,
            "x-amz-date": amz_date,
            "Content-Type": "application/json",
        }

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        url = (
            f"https://bedrock-runtime.{self.region}.amazonaws.com"
            f"/model/{self.model}/invoke"
        )

        anthropic_messages = []
        system_prompt = None
        for m in messages:
            if m.role.value == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({"role": m.role.value, "content": m.content})

        body_dict: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
        }
        if system_prompt:
            body_dict["system"] = system_prompt

        body_bytes = json.dumps(body_dict).encode()
        headers = self._sign_request("POST", url, {}, body_bytes)

        try:
            resp = self._get_session().post(
                url, data=body_bytes, headers=headers,
                timeout=kwargs.get("timeout", 120),
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            raise ProviderError(f"AWS Bedrock API error: {exc}") from exc

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
        )

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["region"] = self.region
        return info
