"""API Key management with secure storage."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional


class APIKeyManager:
    """Centralized API key management with secure storage."""

    SUPPORTED_PROVIDERS = [
        "openai", "anthropic", "groq", "google", "cohere",
        "mistral", "deepseek", "together", "replicate",
        "openrouter", "opencode", "azure_openai", "aws",
    ]

    ENV_MAPPINGS = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "google": "GOOGLE_API_KEY",
        "cohere": "COHERE_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "together": "TOGETHER_API_KEY",
        "replicate": "REPLICATE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "opencode": "OPENCODE_API_KEY",
        "azure_openai": "AZURE_OPENAI_API_KEY",
        "aws": "AWS_ACCESS_KEY_ID",
    }

    def __init__(self, secrets_path: str = None):
        self.secrets_path = Path(secrets_path or Path.home() / ".streamlitforge" / "secrets.toml")
        self._keys: Dict[str, str] = {}
        self._load_keys()

    def _load_keys(self):
        for provider in self.SUPPORTED_PROVIDERS:
            key = self._get_key(provider)
            if key:
                self._keys[provider] = key

    def _get_key(self, provider: str) -> Optional[str]:
        env_var = self.ENV_MAPPINGS.get(provider)
        if env_var:
            key = os.environ.get(env_var)
            if key:
                return key

        env_file = Path.cwd() / ".env"
        if env_file.exists() and env_var:
            key = self._read_env_file(env_file, env_var)
            if key:
                return key

        if self.secrets_path.exists():
            key = self._read_secrets_toml(provider)
            if key:
                return key

        return None

    def _read_env_file(self, path: Path, var: str) -> Optional[str]:
        try:
            content = path.read_text()
            match = re.search(rf"^{re.escape(var)}=(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip().strip('"').strip("'")
        except OSError:
            pass
        return None

    def _read_secrets_toml(self, provider: str) -> Optional[str]:
        try:
            content = self.secrets_path.read_text()
            key_name = f"{provider}_api_key"
            match = re.search(
                rf'^{re.escape(key_name)}\s*=\s*"([^"]*)"', content, re.MULTILINE
            )
            if match:
                return match.group(1)
            match = re.search(
                rf"^{re.escape(key_name)}\s*=\s*'([^']*)'", content, re.MULTILINE
            )
            if match:
                return match.group(1)
        except OSError:
            pass
        return None

    def get(self, provider: str) -> Optional[str]:
        return self._keys.get(provider)

    def has(self, provider: str) -> bool:
        return provider in self._keys

    def set(self, provider: str, key: str, persist: bool = True):
        self._keys[provider] = key
        if persist:
            self._persist_key(provider, key)

    def remove(self, provider: str, persist: bool = True):
        self._keys.pop(provider, None)
        if persist:
            self._remove_from_secrets(provider)

    def _persist_key(self, provider: str, key: str):
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if self.secrets_path.exists():
            for line in self.secrets_path.read_text().splitlines():
                match = re.match(r'^(\w+)\s*=\s*"([^"]*)"', line)
                if match:
                    existing[match.group(1)] = match.group(2)
        existing[f"{provider}_api_key"] = key
        lines = [f'{k} = "{v}"' for k, v in sorted(existing.items())]
        self.secrets_path.write_text("\n".join(lines) + "\n")
        try:
            self.secrets_path.chmod(0o600)
        except OSError:
            pass

    def _remove_from_secrets(self, provider: str):
        if not self.secrets_path.exists():
            return
        key_name = f"{provider}_api_key"
        lines = []
        for line in self.secrets_path.read_text().splitlines():
            if not line.strip().startswith(key_name):
                lines.append(line)
        self.secrets_path.write_text("\n".join(lines) + "\n")

    def list_configured(self) -> List[str]:
        return sorted(self._keys.keys())

    def test_key(self, provider: str) -> bool:
        key = self.get(provider)
        if not key:
            return False
        return True
