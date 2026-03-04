"""Tests for APIKeyManager — no mocks, real functional calls."""

import os
import tempfile
import unittest
from pathlib import Path

from streamlitforge.core.api_keys import APIKeyManager


class TestAPIKeyManagerInit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")

    def test_supported_providers_count(self):
        self.assertEqual(len(APIKeyManager.SUPPORTED_PROVIDERS), 13)

    def test_env_mappings_match_providers(self):
        for provider in APIKeyManager.SUPPORTED_PROVIDERS:
            self.assertIn(provider, APIKeyManager.ENV_MAPPINGS)

    def test_custom_secrets_path(self):
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.secrets_path, Path(self.secrets_path))

    def test_empty_keys_initially(self):
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.list_configured(), [])


class TestGetSetRemove(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")
        self.mgr = APIKeyManager(secrets_path=self.secrets_path)

    def test_get_returns_none_for_unconfigured(self):
        self.assertIsNone(self.mgr.get("openai"))

    def test_has_returns_false_for_unconfigured(self):
        self.assertFalse(self.mgr.has("openai"))

    def test_set_and_get(self):
        self.mgr.set("openai", "sk-test-key-123")
        self.assertEqual(self.mgr.get("openai"), "sk-test-key-123")

    def test_set_updates_has(self):
        self.mgr.set("openai", "sk-test-key-123")
        self.assertTrue(self.mgr.has("openai"))

    def test_remove_clears_key(self):
        self.mgr.set("openai", "sk-test-key-123")
        self.mgr.remove("openai")
        self.assertIsNone(self.mgr.get("openai"))
        self.assertFalse(self.mgr.has("openai"))

    def test_remove_nonexistent_is_noop(self):
        self.mgr.remove("nonexistent")

    def test_set_without_persist(self):
        self.mgr.set("openai", "sk-temp", persist=False)
        self.assertEqual(self.mgr.get("openai"), "sk-temp")
        self.assertFalse(Path(self.secrets_path).exists())

    def test_list_configured_sorted(self):
        self.mgr.set("groq", "gsk-123", persist=False)
        self.mgr.set("anthropic", "sk-ant-123", persist=False)
        configured = self.mgr.list_configured()
        self.assertEqual(configured, ["anthropic", "groq"])


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")

    def test_persist_creates_file(self):
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        mgr.set("openai", "sk-test-key-123")
        self.assertTrue(Path(self.secrets_path).exists())

    def test_persisted_key_survives_reload(self):
        mgr1 = APIKeyManager(secrets_path=self.secrets_path)
        mgr1.set("openai", "sk-test-key-123")
        mgr2 = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr2.get("openai"), "sk-test-key-123")

    def test_multiple_keys_persist(self):
        mgr1 = APIKeyManager(secrets_path=self.secrets_path)
        mgr1.set("openai", "sk-openai-123")
        mgr1.set("anthropic", "sk-ant-456")
        mgr2 = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr2.get("openai"), "sk-openai-123")
        self.assertEqual(mgr2.get("anthropic"), "sk-ant-456")

    def test_remove_persists(self):
        mgr1 = APIKeyManager(secrets_path=self.secrets_path)
        mgr1.set("openai", "sk-test-key-123")
        mgr1.set("anthropic", "sk-ant-456")
        mgr1.remove("openai")
        mgr2 = APIKeyManager(secrets_path=self.secrets_path)
        self.assertIsNone(mgr2.get("openai"))
        self.assertEqual(mgr2.get("anthropic"), "sk-ant-456")

    def test_file_permissions(self):
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        mgr.set("openai", "sk-test-key-123")
        mode = Path(self.secrets_path).stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_secrets_toml_format(self):
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        mgr.set("openai", "sk-test-key-123")
        content = Path(self.secrets_path).read_text()
        self.assertIn('openai_api_key = "sk-test-key-123"', content)


class TestEnvLoading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")
        self._old_env = {}

    def tearDown(self):
        for key, val in self._old_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def test_env_variable_loading(self):
        env_key = "OPENAI_API_KEY"
        self._old_env[env_key] = os.environ.get(env_key)
        os.environ[env_key] = "sk-from-env"
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.get("openai"), "sk-from-env")

    def test_env_takes_priority_over_secrets(self):
        mgr1 = APIKeyManager(secrets_path=self.secrets_path)
        mgr1.set("openai", "sk-from-file")
        env_key = "OPENAI_API_KEY"
        self._old_env[env_key] = os.environ.get(env_key)
        os.environ[env_key] = "sk-from-env"
        mgr2 = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr2.get("openai"), "sk-from-env")


class TestDotEnvLoading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")
        self._original_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._original_cwd)

    def test_dotenv_loading(self):
        env_file = Path(self.tmp) / ".env"
        env_file.write_text('GROQ_API_KEY=gsk-from-dotenv\n')
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.get("groq"), "gsk-from-dotenv")

    def test_dotenv_with_quotes(self):
        env_file = Path(self.tmp) / ".env"
        env_file.write_text('GROQ_API_KEY="gsk-quoted"\n')
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.get("groq"), "gsk-quoted")


class TestSecretsTomlReading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")

    def test_reads_double_quoted(self):
        Path(self.secrets_path).write_text('openai_api_key = "sk-double"\n')
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.get("openai"), "sk-double")

    def test_reads_single_quoted(self):
        Path(self.secrets_path).write_text("openai_api_key = 'sk-single'\n")
        mgr = APIKeyManager(secrets_path=self.secrets_path)
        self.assertEqual(mgr.get("openai"), "sk-single")


class TestTestKey(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.secrets_path = os.path.join(self.tmp, "secrets.toml")
        self.mgr = APIKeyManager(secrets_path=self.secrets_path)

    def test_returns_false_if_not_configured(self):
        self.assertFalse(self.mgr.test_key("openai"))

    def test_returns_true_if_configured(self):
        self.mgr.set("openai", "sk-test-key", persist=False)
        self.assertTrue(self.mgr.test_key("openai"))


if __name__ == "__main__":
    unittest.main()
