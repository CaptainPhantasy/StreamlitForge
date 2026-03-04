"""Tests for LLM base classes, circuit breaker, cache, and router — no mocks."""

import os
import tempfile
import time
import unittest

from streamlitforge.llm.base import (
    AllProvidersFailedError,
    CircuitBreaker,
    LLMError,
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
    ProviderError,
    ProviderStatus,
)
from streamlitforge.llm.cache import ResponseCache
from streamlitforge.llm.router import (
    ANALYSIS_BONUSES,
    CODE_BONUSES,
    PROVIDER_PRIORITY,
    QUALITY_RANKINGS,
    EnhancedLLMRouter,
    _get_base_weight,
)


# ---------------------------------------------------------------------------
# Concrete provider for testing (no network, fully deterministic)
# ---------------------------------------------------------------------------

class StubProvider(LLMProvider):
    """Concrete provider that returns canned responses for testing."""

    PROVIDER_NAME = "stub"
    SUPPORTS_STREAMING = False
    SUPPORTS_TOOLS = False
    SUPPORTS_VISION = False

    def __init__(self, response_text="stub response", available=True, cost=0.0, fail=False):
        self._response_text = response_text
        self._available = available
        self._cost = cost
        self._fail = fail
        self.call_count = 0

    def generate(self, messages, **kwargs):
        self.call_count += 1
        if self._fail:
            raise ProviderError("Stub provider forced failure")
        return LLMResponse(
            content=self._response_text,
            provider=self.PROVIDER_NAME,
            model="stub-model",
            tokens_used=10,
            cost_estimate=self._cost,
        )

    def is_available(self):
        return self._available

    def estimate_cost(self, tokens):
        return self._cost


class StubVisionProvider(StubProvider):
    PROVIDER_NAME = "stub_vision"
    SUPPORTS_VISION = True
    SUPPORTS_TOOLS = True


# ===========================================================================
# MessageRole / Message / LLMResponse dataclasses
# ===========================================================================

class TestMessageRole(unittest.TestCase):
    def test_values(self):
        self.assertEqual(MessageRole.SYSTEM.value, "system")
        self.assertEqual(MessageRole.USER.value, "user")
        self.assertEqual(MessageRole.ASSISTANT.value, "assistant")

    def test_enum_members(self):
        self.assertEqual(len(MessageRole), 3)


class TestMessage(unittest.TestCase):
    def test_creation(self):
        m = Message(role=MessageRole.USER, content="Hello")
        self.assertEqual(m.role, MessageRole.USER)
        self.assertEqual(m.content, "Hello")


class TestLLMResponse(unittest.TestCase):
    def test_defaults(self):
        r = LLMResponse(content="hi", provider="p", model="m")
        self.assertIsNone(r.tokens_used)
        self.assertIsNone(r.latency_ms)
        self.assertFalse(r.cached)
        self.assertIsNone(r.cost_estimate)
        self.assertIsNone(r.finish_reason)

    def test_all_fields(self):
        r = LLMResponse(
            content="x", provider="p", model="m",
            tokens_used=100, latency_ms=50, cached=True,
            cost_estimate=0.01, finish_reason="stop",
        )
        self.assertEqual(r.tokens_used, 100)
        self.assertTrue(r.cached)


class TestProviderStatus(unittest.TestCase):
    def test_defaults(self):
        s = ProviderStatus(name="test", available=True)
        self.assertIsNone(s.latency_ms)
        self.assertIsNone(s.error)
        self.assertEqual(s.model_count, 0)


# ===========================================================================
# Exception hierarchy
# ===========================================================================

class TestExceptions(unittest.TestCase):
    def test_hierarchy(self):
        self.assertTrue(issubclass(ProviderError, LLMError))
        self.assertTrue(issubclass(AllProvidersFailedError, LLMError))
        self.assertTrue(issubclass(LLMError, Exception))


# ===========================================================================
# LLMProvider ABC
# ===========================================================================

class TestLLMProviderABC(unittest.TestCase):
    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            LLMProvider()

    def test_concrete_subclass(self):
        p = StubProvider()
        self.assertEqual(p.name, "stub")
        self.assertEqual(p.estimate_cost(1000), 0.0)
        self.assertTrue(p.is_available())

    def test_health_check(self):
        p = StubProvider()
        status = p.health_check()
        self.assertIsInstance(status, ProviderStatus)
        self.assertEqual(status.name, "stub")
        self.assertTrue(status.available)
        self.assertIsNotNone(status.latency_ms)

    def test_health_check_unavailable(self):
        p = StubProvider(available=False)
        status = p.health_check()
        self.assertFalse(status.available)

    def test_get_model_info(self):
        p = StubProvider()
        info = p.get_model_info()
        self.assertEqual(info["provider"], "stub")
        self.assertIn("streaming", info)
        self.assertIn("tools", info)
        self.assertIn("vision", info)


# ===========================================================================
# CircuitBreaker
# ===========================================================================

class TestCircuitBreaker(unittest.TestCase):
    def test_starts_closed(self):
        cb = CircuitBreaker()
        self.assertEqual(cb.state, "CLOSED")
        self.assertFalse(cb.is_open())

    def test_opens_after_threshold(self):
        cb = CircuitBreaker()
        for _ in range(CircuitBreaker.FAILURE_THRESHOLD):
            cb.record_failure()
        self.assertEqual(cb.state, "OPEN")
        self.assertTrue(cb.is_open())

    def test_below_threshold_stays_closed(self):
        cb = CircuitBreaker()
        for _ in range(CircuitBreaker.FAILURE_THRESHOLD - 1):
            cb.record_failure()
        self.assertEqual(cb.state, "CLOSED")
        self.assertFalse(cb.is_open())

    def test_success_resets(self):
        cb = CircuitBreaker()
        for _ in range(CircuitBreaker.FAILURE_THRESHOLD):
            cb.record_failure()
        self.assertTrue(cb.is_open())
        cb.record_success()
        self.assertEqual(cb.state, "CLOSED")
        self.assertFalse(cb.is_open())
        self.assertEqual(cb.failures, 0)

    def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker()
        for _ in range(CircuitBreaker.FAILURE_THRESHOLD):
            cb.record_failure()
        # Simulate time passing beyond recovery timeout
        cb.last_failure_time = time.time() - CircuitBreaker.RECOVERY_TIMEOUT - 1
        self.assertFalse(cb.is_open())
        self.assertEqual(cb.state, "HALF_OPEN")


# ===========================================================================
# ResponseCache
# ===========================================================================

class TestResponseCache(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_cache.db")
        self.cache = ResponseCache(db_path=self.db_path, ttl_hours=1)

    def test_set_and_get(self):
        self.cache.set("hello", None, "world")
        result = self.cache.get("hello")
        self.assertEqual(result, "world")

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_system_prompt_included_in_key(self):
        self.cache.set("hello", "sys1", "response1")
        self.cache.set("hello", "sys2", "response2")
        self.assertEqual(self.cache.get("hello", "sys1"), "response1")
        self.assertEqual(self.cache.get("hello", "sys2"), "response2")

    def test_expired_entry_returns_none(self):
        cache = ResponseCache(db_path=self.db_path, ttl_hours=0)
        cache.set("key", None, "value")
        # TTL is 0 hours = 0 seconds, so immediately expired
        self.assertIsNone(cache.get("key"))

    def test_clear(self):
        self.cache.set("a", None, "1")
        self.cache.set("b", None, "2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("a"))
        self.assertIsNone(self.cache.get("b"))

    def test_cleanup_expired(self):
        cache = ResponseCache(db_path=self.db_path, ttl_hours=0)
        cache.set("expired", None, "old")
        removed = cache.cleanup_expired()
        self.assertGreaterEqual(removed, 1)

    def test_get_stats(self):
        self.cache.set("x", None, "y")
        stats = self.cache.get_stats()
        self.assertEqual(stats["total_entries"], 1)
        self.assertIn("valid_entries", stats)
        self.assertIn("expired_entries", stats)
        self.assertIn("total_accesses", stats)
        self.assertIn("db_path", stats)
        self.assertIn("ttl_hours", stats)

    def test_access_count_increments(self):
        self.cache.set("test", None, "val")
        self.cache.get("test")
        self.cache.get("test")
        stats = self.cache.get_stats()
        self.assertGreaterEqual(stats["total_accesses"], 3)  # 1 initial + 2 gets

    def test_overwrite_entry(self):
        self.cache.set("key", None, "old")
        self.cache.set("key", None, "new")
        self.assertEqual(self.cache.get("key"), "new")


# ===========================================================================
# Provider Priority data
# ===========================================================================

class TestProviderPriority(unittest.TestCase):
    def test_all_tiers_present(self):
        expected_tiers = ["local", "free_cloud", "curated", "aggregators", "paid", "enterprise", "fallback"]
        for tier in expected_tiers:
            self.assertIn(tier, PROVIDER_PRIORITY)

    def test_ollama_highest_weight(self):
        self.assertEqual(PROVIDER_PRIORITY["local"]["ollama"]["weight"], 100)

    def test_pattern_library_lowest(self):
        self.assertEqual(PROVIDER_PRIORITY["fallback"]["pattern_library"]["weight"], 10)

    def test_get_base_weight_known(self):
        self.assertEqual(_get_base_weight("ollama"), 100.0)
        self.assertEqual(_get_base_weight("openai"), 60.0)

    def test_get_base_weight_unknown(self):
        self.assertEqual(_get_base_weight("nonexistent"), 50.0)


# ===========================================================================
# EnhancedLLMRouter
# ===========================================================================

class TestEnhancedLLMRouter(unittest.TestCase):
    def test_empty_router(self):
        router = EnhancedLLMRouter()
        self.assertEqual(len(router.providers), 0)

    def test_add_provider(self):
        router = EnhancedLLMRouter()
        router.add_provider("test", StubProvider())
        self.assertIn("test", router.providers)
        self.assertIn("test", router.circuit_breakers)

    def test_remove_provider(self):
        router = EnhancedLLMRouter(providers={"test": StubProvider()})
        router.remove_provider("test")
        self.assertNotIn("test", router.providers)

    def test_generate_single_provider(self):
        p = StubProvider(response_text="hello from stub")
        router = EnhancedLLMRouter(providers={"stub": p})
        result = router.generate("test prompt", use_cache=False)
        self.assertEqual(result.content, "hello from stub")
        self.assertEqual(result.provider, "stub")
        self.assertEqual(p.call_count, 1)

    def test_generate_with_system_prompt(self):
        p = StubProvider(response_text="answer")
        router = EnhancedLLMRouter(providers={"stub": p})
        result = router.generate("q", system_prompt="be helpful", use_cache=False)
        self.assertEqual(result.content, "answer")

    def test_generate_uses_cache(self):
        tmpdir = tempfile.mkdtemp()
        cache = ResponseCache(db_path=os.path.join(tmpdir, "c.db"))
        p = StubProvider()
        router = EnhancedLLMRouter(providers={"stub": p}, cache=cache)
        # First call hits provider
        r1 = router.generate("cached_prompt")
        self.assertFalse(r1.cached)
        self.assertEqual(p.call_count, 1)
        # Second call hits cache
        r2 = router.generate("cached_prompt")
        self.assertTrue(r2.cached)
        self.assertEqual(r2.provider, "cache")
        self.assertEqual(p.call_count, 1)  # not called again

    def test_generate_fallback_on_failure(self):
        failing = StubProvider(fail=True)
        success = StubProvider(response_text="fallback response")
        router = EnhancedLLMRouter(
            providers={"fail": failing, "ok": success}
        )
        result = router.generate("test", use_cache=False)
        self.assertEqual(result.content, "fallback response")
        self.assertEqual(failing.call_count, 1)
        self.assertEqual(success.call_count, 1)

    def test_generate_all_fail_raises(self):
        p1 = StubProvider(fail=True)
        p2 = StubProvider(fail=True)
        router = EnhancedLLMRouter(providers={"p1": p1, "p2": p2})
        with self.assertRaises(AllProvidersFailedError):
            router.generate("test", use_cache=False)

    def test_generate_no_providers_raises(self):
        router = EnhancedLLMRouter()
        with self.assertRaises(AllProvidersFailedError):
            router.generate("test", use_cache=False)

    def test_circuit_breaker_blocks_provider(self):
        p = StubProvider(fail=True)
        router = EnhancedLLMRouter(providers={"p": p})
        # Trigger failures to open circuit breaker
        for _ in range(CircuitBreaker.FAILURE_THRESHOLD):
            try:
                router.generate("test", use_cache=False)
            except AllProvidersFailedError:
                pass
        # Circuit should be open now
        self.assertTrue(router.circuit_breakers["p"].is_open())

    def test_select_provider_basic(self):
        p = StubProvider()
        router = EnhancedLLMRouter(providers={"stub": p})
        selected = router.select_provider()
        self.assertIs(selected, p)

    def test_select_provider_none_available(self):
        p = StubProvider(available=False)
        router = EnhancedLLMRouter(providers={"stub": p})
        router.provider_status["stub"] = ProviderStatus(name="stub", available=False)
        selected = router.select_provider()
        self.assertIsNone(selected)

    def test_select_provider_feature_filter(self):
        plain = StubProvider()
        vision = StubVisionProvider()
        router = EnhancedLLMRouter(providers={"plain": plain, "vision": vision})
        selected = router.select_provider(required_features=["vision"])
        self.assertIs(selected, vision)

    def test_get_available_providers(self):
        p1 = StubProvider(available=True)
        p2 = StubProvider(available=False)
        router = EnhancedLLMRouter(providers={"avail": p1, "unavail": p2})
        avail = router.get_available_providers()
        self.assertIn("avail", avail)
        self.assertNotIn("unavail", avail)

    def test_get_status_report(self):
        p = StubProvider()
        router = EnhancedLLMRouter(providers={"p": p}, strategy="cost_optimized")
        report = router.get_status_report()
        self.assertIn("providers", report)
        self.assertIn("strategy", report)
        self.assertEqual(report["strategy"], "cost_optimized")

    def test_refresh_status(self):
        p = StubProvider()
        router = EnhancedLLMRouter(providers={"p": p})
        router.refresh_status()
        self.assertIn("p", router.provider_status)
        self.assertTrue(router.provider_status["p"].available)

    def test_strategy_quality_optimized(self):
        cheap = StubProvider(cost=0.0)
        router = EnhancedLLMRouter(
            providers={"cheap": cheap}, strategy="quality_optimized"
        )
        selected = router.select_provider(prefer_quality=True)
        self.assertIsNotNone(selected)

    def test_strategy_latency_optimized(self):
        p = StubProvider()
        router = EnhancedLLMRouter(
            providers={"p": p}, strategy="latency_optimized"
        )
        router.provider_status["p"] = ProviderStatus(name="p", available=True, latency_ms=50)
        selected = router.select_provider(prefer_speed=True)
        self.assertIsNotNone(selected)

    def test_max_cost_filter(self):
        expensive = StubProvider(cost=100.0)
        router = EnhancedLLMRouter(providers={"exp": expensive})
        selected = router.select_provider(max_cost=0.01)
        # Should still return it (just with penalty), since it's the only one
        self.assertIsNotNone(selected)

    def test_task_type_code_bonuses(self):
        # Just verify the data exists
        self.assertIn("deepseek", CODE_BONUSES)
        self.assertIn("anthropic", ANALYSIS_BONUSES)
        self.assertIn("anthropic", QUALITY_RANKINGS)


# ===========================================================================
# Provider Registry
# ===========================================================================

class TestProviderRegistry(unittest.TestCase):
    def test_all_providers_registered(self):
        from streamlitforge.llm.providers import list_provider_names, get_provider_class
        names = list_provider_names()
        self.assertGreaterEqual(len(names), 20)
        expected = [
            "ollama", "lmstudio", "vllm", "localai", "jan",
            "groq", "openai", "anthropic", "google", "cohere",
            "mistral", "deepseek", "together", "replicate",
            "openrouter", "opencode_go", "opencode_zen",
            "azure_openai", "aws_bedrock", "pattern_library",
        ]
        for name in expected:
            self.assertIn(name, names, f"Provider '{name}' not registered")
            cls = get_provider_class(name)
            self.assertIsNotNone(cls, f"Provider class for '{name}' is None")

    def test_provider_classes_are_llmprovider_subclasses(self):
        from streamlitforge.llm.providers import list_provider_names, get_provider_class
        for name in list_provider_names():
            cls = get_provider_class(name)
            self.assertTrue(
                issubclass(cls, LLMProvider),
                f"{name} -> {cls} is not a subclass of LLMProvider",
            )


# ===========================================================================
# OpenAI-compatible base class
# ===========================================================================

class TestOpenAICompatibleProvider(unittest.TestCase):
    def test_init(self):
        from streamlitforge.llm.providers._openai_compat import OpenAICompatibleProvider

        class ConcreteOAI(OpenAICompatibleProvider):
            def is_available(self):
                return True

        p = ConcreteOAI(
            base_url="http://localhost:1234/v1",
            api_key="test-key",
            model="test-model",
        )
        self.assertEqual(p.base_url, "http://localhost:1234/v1")
        self.assertEqual(p.model, "test-model")

    def test_is_abstract(self):
        from streamlitforge.llm.providers._openai_compat import OpenAICompatibleProvider
        with self.assertRaises(TypeError):
            OpenAICompatibleProvider(base_url="http://localhost:1")

    def test_get_model_info(self):
        from streamlitforge.llm.providers._openai_compat import OpenAICompatibleProvider

        class ConcreteOAI(OpenAICompatibleProvider):
            def is_available(self):
                return False

        p = ConcreteOAI(base_url="http://test:1234/v1", model="m")
        info = p.get_model_info()
        self.assertIn("base_url", info)

    def test_generate_unreachable_raises(self):
        from streamlitforge.llm.providers._openai_compat import OpenAICompatibleProvider

        class ConcreteOAI(OpenAICompatibleProvider):
            def is_available(self):
                return True

        p = ConcreteOAI(base_url="http://127.0.0.1:1/v1", model="m", timeout=1)
        msgs = [Message(MessageRole.USER, "hello")]
        with self.assertRaises(ProviderError):
            p.generate(msgs, timeout=1)


# ===========================================================================
# Individual Provider classes (construction only, no network)
# ===========================================================================

class TestProviderConstruction(unittest.TestCase):
    """Test that each provider can be constructed with defaults."""

    def test_ollama_provider(self):
        from streamlitforge.llm.providers.ollama import OllamaProvider
        p = OllamaProvider()
        self.assertEqual(p.PROVIDER_NAME, "ollama")
        self.assertEqual(p.model, "codellama:7b")
        info = p.get_model_info()
        self.assertIn("base_url", info)

    def test_lmstudio_provider(self):
        from streamlitforge.llm.providers.lmstudio import LMStudioProvider
        p = LMStudioProvider()
        self.assertEqual(p.PROVIDER_NAME, "lmstudio")

    def test_groq_provider(self):
        from streamlitforge.llm.providers.groq import GroqProvider
        p = GroqProvider(api_key="test")
        self.assertEqual(p.PROVIDER_NAME, "groq")
        self.assertTrue(p.is_available())

    def test_groq_not_available_without_key(self):
        from streamlitforge.llm.providers.groq import GroqProvider
        p = GroqProvider()
        self.assertFalse(p.is_available())

    def test_openai_provider(self):
        from streamlitforge.llm.providers.openai import OpenAIProvider
        p = OpenAIProvider(api_key="sk-test")
        self.assertEqual(p.PROVIDER_NAME, "openai")
        self.assertTrue(p.is_available())

    def test_anthropic_provider(self):
        from streamlitforge.llm.providers.anthropic import AnthropicProvider
        p = AnthropicProvider(api_key="sk-ant-test")
        self.assertEqual(p.PROVIDER_NAME, "anthropic")

    def test_google_provider(self):
        from streamlitforge.llm.providers.google import GoogleProvider
        p = GoogleProvider(api_key="AI-test")
        self.assertEqual(p.PROVIDER_NAME, "google")

    def test_cohere_provider(self):
        from streamlitforge.llm.providers.cohere import CohereProvider
        p = CohereProvider(api_key="co-test")
        self.assertEqual(p.PROVIDER_NAME, "cohere")

    def test_deepseek_provider(self):
        from streamlitforge.llm.providers.deepseek import DeepSeekProvider
        p = DeepSeekProvider(api_key="test")
        self.assertEqual(p.PROVIDER_NAME, "deepseek")

    def test_openrouter_provider(self):
        from streamlitforge.llm.providers.openrouter import OpenRouterProvider as ORProvider
        p = ORProvider(api_key="test")
        self.assertEqual(p.PROVIDER_NAME, "openrouter")
        self.assertTrue(p.estimate_cost(1000) >= 0)

    def test_opencode_go_provider(self):
        from streamlitforge.llm.providers.opencode import OpenCodeGoProvider
        p = OpenCodeGoProvider(api_key="test")
        self.assertEqual(p.PROVIDER_NAME, "opencode_go")

    def test_opencode_zen_provider(self):
        from streamlitforge.llm.providers.opencode import OpenCodeZenProvider
        p = OpenCodeZenProvider(api_key="test")
        self.assertEqual(p.PROVIDER_NAME, "opencode_zen")

    def test_pattern_library_provider(self):
        from streamlitforge.llm.providers.pattern_library import PatternLibraryProvider
        p = PatternLibraryProvider()
        self.assertEqual(p.PROVIDER_NAME, "pattern_library")


if __name__ == "__main__":
    unittest.main()
