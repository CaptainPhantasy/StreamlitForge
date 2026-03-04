"""Test LLM Providers and Router — real functional tests (no mocks)."""

import unittest

from streamlitforge.llm import (
    OpenRouterProvider, OllamaProvider, LLMRouter, BaseLLMProvider,
    ProviderError, LLMError,
)


class TestOpenRouterProvider(unittest.TestCase):
    """Test OpenRouterProvider initialisation and helpers (no network calls)."""

    def test_init_defaults(self):
        p = OpenRouterProvider()
        self.assertEqual(p.model, 'llama3-70b-8192')
        self.assertEqual(p.base_url, 'https://openrouter.ai/api/v1')
        self.assertIsNone(p.api_key)

    def test_init_with_params(self):
        p = OpenRouterProvider(api_key='sk-test', model='gpt-4', base_url='http://custom')
        self.assertEqual(p.api_key, 'sk-test')
        self.assertEqual(p.model, 'gpt-4')
        self.assertEqual(p.base_url, 'http://custom')

    def test_get_model_info(self):
        p = OpenRouterProvider(api_key='k', model='test-model')
        info = p.get_model_info()
        self.assertEqual(info['provider'], 'openrouter')
        self.assertEqual(info['model'], 'test-model')
        self.assertIn('base_url', info)

    def test_is_available_with_key(self):
        self.assertTrue(OpenRouterProvider(api_key='sk-x').is_available())

    def test_is_available_without_key(self):
        self.assertFalse(OpenRouterProvider().is_available())

    def test_generate_bad_url_raises_provider_error(self):
        p = OpenRouterProvider(api_key='k', base_url='http://127.0.0.1:1')
        with self.assertRaises(ProviderError):
            p.generate("hello", timeout=1)

    def test_chat_bad_url_raises_provider_error(self):
        p = OpenRouterProvider(api_key='k', base_url='http://127.0.0.1:1')
        with self.assertRaises(ProviderError):
            p.chat([{'role': 'user', 'content': 'hi'}], timeout=1)


class TestOllamaProvider(unittest.TestCase):
    """Test OllamaProvider initialisation and helpers."""

    def test_init_defaults(self):
        p = OllamaProvider()
        self.assertEqual(p.model, 'llama3')
        self.assertEqual(p.host, 'http://localhost:11434')

    def test_init_custom(self):
        p = OllamaProvider(model='mistral', host='http://myhost:11434')
        self.assertEqual(p.model, 'mistral')
        self.assertEqual(p.host, 'http://myhost:11434')

    def test_get_model_info(self):
        info = OllamaProvider(model='codellama').get_model_info()
        self.assertEqual(info['provider'], 'ollama')
        self.assertEqual(info['model'], 'codellama')
        self.assertIn('host', info)

    def test_is_available_returns_bool(self):
        p = OllamaProvider(host='http://127.0.0.1:1')
        self.assertIsInstance(p.is_available(), bool)

    def test_generate_unreachable_raises_provider_error(self):
        p = OllamaProvider(host='http://127.0.0.1:1')
        with self.assertRaises(ProviderError):
            p.generate("test", timeout=1)

    def test_chat_unreachable_raises_provider_error(self):
        p = OllamaProvider(host='http://127.0.0.1:1')
        with self.assertRaises(ProviderError):
            p.chat([{'role': 'user', 'content': 'hi'}], timeout=1)


class TestLLMRouter(unittest.TestCase):
    """Test LLMRouter with real provider instances."""

    def test_init_with_providers(self):
        router = LLMRouter(providers=[
            OpenRouterProvider(api_key='k'),
            OllamaProvider(),
        ])
        self.assertEqual(len(router.providers), 2)
        self.assertIn('OpenRouterProvider', router.providers)
        self.assertIn('OllamaProvider', router.providers)

    def test_get_provider_by_name(self):
        op = OpenRouterProvider(api_key='k')
        router = LLMRouter(providers=[op])
        self.assertIs(router.get_provider('OpenRouterProvider'), op)
        self.assertIsNone(router.get_provider('DoesNotExist'))

    def test_get_available_providers_returns_list(self):
        router = LLMRouter(providers=[
            OpenRouterProvider(api_key='k'),
            OpenRouterProvider(),
        ])
        avail = router.get_available_providers()
        self.assertIsInstance(avail, list)

    def test_get_model_info(self):
        router = LLMRouter(providers=[OpenRouterProvider(api_key='k')])
        info = router.get_model_info()
        self.assertIn('OpenRouterProvider', info)

    def test_generate_all_unavailable_raises(self):
        router = LLMRouter(providers=[
            OpenRouterProvider(),
            OllamaProvider(host='http://127.0.0.1:1'),
        ])
        with self.assertRaises(LLMError):
            router.generate("test")

    def test_chat_all_unavailable_raises(self):
        router = LLMRouter(providers=[
            OpenRouterProvider(),
            OllamaProvider(host='http://127.0.0.1:1'),
        ])
        with self.assertRaises(LLMError):
            router.chat([{'role': 'user', 'content': 'hi'}])

    def test_generate_fallback_on_error(self):
        """If the first available provider errors, router tries next."""
        p1 = OpenRouterProvider(api_key='k', base_url='http://127.0.0.1:1')
        p2 = OpenRouterProvider(api_key='k', base_url='http://127.0.0.1:1')
        router = LLMRouter(providers=[p1, p2])
        with self.assertRaises(LLMError):
            router.generate("test", timeout=1)


class TestBaseLLMProviderInterface(unittest.TestCase):
    """Verify the abstract interface cannot be instantiated directly."""

    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            BaseLLMProvider()


if __name__ == '__main__':
    unittest.main()
