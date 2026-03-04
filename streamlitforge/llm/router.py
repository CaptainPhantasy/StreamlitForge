"""Enhanced LLM Router with provider priority, circuit breakers, and strategy selection."""

import logging
import time
from typing import Any, Dict, List, Optional

from .base import (
    AllProvidersFailedError,
    CircuitBreaker,
    LLMProvider,
    LLMResponse,
    Message,
    MessageRole,
    ProviderStatus,
)

logger = logging.getLogger(__name__)

PROVIDER_PRIORITY = {
    "local": {
        "ollama": {"weight": 100, "check": "http://localhost:11434/api/tags"},
        "lmstudio": {"weight": 99, "check": "http://localhost:1234/v1/models"},
        "vllm": {"weight": 98, "check": "http://localhost:8000/v1/models"},
        "localai": {"weight": 97, "check": "http://localhost:8080/v1/models"},
        "jan": {"weight": 96, "check": "http://localhost:1337/v1/models"},
    },
    "free_cloud": {
        "groq": {"weight": 90, "requires_key": True, "free_tier": True},
        "google": {"weight": 85, "requires_key": True, "free_tier": True},
        "cohere": {"weight": 80, "requires_key": True, "free_tier": True},
        "together": {"weight": 75, "requires_key": True, "free_tier": False},
    },
    "curated": {
        "opencode_go": {"weight": 72, "requires_key": True},
        "opencode_zen": {"weight": 68, "requires_key": True},
    },
    "aggregators": {
        "openrouter": {"weight": 70, "requires_key": True},
    },
    "paid": {
        "openai": {"weight": 60, "requires_key": True},
        "anthropic": {"weight": 55, "requires_key": True},
        "mistral": {"weight": 50, "requires_key": True},
        "deepseek": {"weight": 45, "requires_key": True},
        "replicate": {"weight": 40, "requires_key": True},
    },
    "enterprise": {
        "azure_openai": {"weight": 35, "requires_key": True},
        "aws_bedrock": {"weight": 30, "requires_key": True},
    },
    "fallback": {
        "cache": {"weight": 20, "always_available": True},
        "pattern_library": {"weight": 10, "always_available": True},
    },
}

QUALITY_RANKINGS = {
    "anthropic": 15,
    "openai": 12,
    "google": 10,
    "opencode_zen": 9,
    "mistral": 8,
    "opencode_go": 7,
    "groq": 5,
    "deepseek": 5,
}

CODE_BONUSES = {"deepseek": 10, "openai": 8, "anthropic": 7, "opencode_go": 6}
ANALYSIS_BONUSES = {"anthropic": 10, "openai": 8, "google": 5}


def _get_base_weight(name: str) -> float:
    for tier in PROVIDER_PRIORITY.values():
        if name in tier:
            return float(tier[name]["weight"])
    return 50.0


class EnhancedLLMRouter:
    """Intelligent router with provider selection, fallback, and optimization."""

    def __init__(
        self,
        providers: Optional[Dict[str, LLMProvider]] = None,
        strategy: str = "cost_optimized",
        cache=None,
        pattern_library=None,
    ):
        self.providers: Dict[str, LLMProvider] = providers or {}
        self.provider_status: Dict[str, ProviderStatus] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            name: CircuitBreaker() for name in self.providers
        }
        self.strategy = strategy
        self.cache = cache
        self.pattern_library = pattern_library
        
        # Cost tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.session_stats: Dict[str, Dict] = {}

    def add_provider(self, name: str, provider: LLMProvider):
        self.providers[name] = provider
        self.circuit_breakers[name] = CircuitBreaker()

    def remove_provider(self, name: str):
        self.providers.pop(name, None)
        self.circuit_breakers.pop(name, None)
        self.provider_status.pop(name, None)

    def select_provider(
        self,
        task_type: str = "general",
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        max_cost: Optional[float] = None,
        required_features: Optional[List[str]] = None,
    ) -> Optional[LLMProvider]:
        candidates = []
        for name, provider in self.providers.items():
            if self.circuit_breakers.get(name, CircuitBreaker()).is_open():
                continue
            status = self.provider_status.get(name)
            if status and not status.available:
                continue
            if required_features:
                if "vision" in required_features and not provider.SUPPORTS_VISION:
                    continue
                if "tools" in required_features and not provider.SUPPORTS_TOOLS:
                    continue
            score = self._calculate_score(
                name, provider, task_type, prefer_speed, prefer_quality, max_cost
            )
            candidates.append((score, name, provider))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][2] if candidates else None

    def _calculate_score(
        self,
        name: str,
        provider: LLMProvider,
        task_type: str,
        prefer_speed: bool,
        prefer_quality: bool,
        max_cost: Optional[float],
    ) -> float:
        score = _get_base_weight(name)

        if self.strategy == "cost_optimized":
            cost = provider.estimate_cost(1000)
            if cost == 0:
                score += 20
            else:
                score -= cost * 10
        elif self.strategy == "latency_optimized" or prefer_speed:
            status = self.provider_status.get(name)
            if status and status.latency_ms:
                score += max(0, 50 - status.latency_ms / 100)
        elif self.strategy == "quality_optimized" or prefer_quality:
            score += QUALITY_RANKINGS.get(name, 0)

        if task_type == "code":
            score += CODE_BONUSES.get(name, 0)
        elif task_type == "analysis":
            score += ANALYSIS_BONUSES.get(name, 0)

        if max_cost is not None:
            cost = provider.estimate_cost(1000)
            if cost > max_cost:
                score -= 50

        return score

    def _get_provider_order(self, task_type: str, kwargs: dict) -> List[str]:
        prefer_speed = kwargs.pop("prefer_speed", False)
        prefer_quality = kwargs.pop("prefer_quality", False)
        max_cost = kwargs.pop("max_cost", None)

        scored = []
        for name in self.providers:
            provider = self.providers[name]
            score = self._calculate_score(
                name, provider, task_type, prefer_speed, prefer_quality, max_cost
            )
            scored.append((score, name))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [name for _, name in scored]

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        task_type: str = "general",
        use_cache: bool = True,
        fallback_to_patterns: bool = True,
        **kwargs,
    ) -> LLMResponse:
        if use_cache and self.cache:
            cached = self.cache.get(prompt, system_prompt)
            if cached:
                return LLMResponse(
                    content=cached,
                    provider="cache",
                    model="cached",
                    cached=True,
                )

        messages: List[Message] = []
        if system_prompt:
            messages.append(Message(MessageRole.SYSTEM, system_prompt))
        messages.append(Message(MessageRole.USER, prompt))

        errors: List[tuple] = []
        provider_order = self._get_provider_order(task_type, kwargs)

        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            cb = self.circuit_breakers.get(provider_name)
            if cb and cb.is_open():
                continue

            try:
                start_time = time.time()
                response = provider.generate(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                response.latency_ms = int((time.time() - start_time) * 1000)

                # Track costs
                self.total_requests += 1
                if response.tokens_used:
                    self.total_tokens += response.tokens_used
                if response.cost_estimate:
                    self.total_cost += response.cost_estimate
                else:
                    # Estimate cost if not provided
                    estimated_cost = provider.estimate_cost(response.tokens_used or 1000)
                    response.cost_estimate = estimated_cost
                    self.total_cost += estimated_cost

                if use_cache and self.cache:
                    self.cache.set(prompt, system_prompt, response.content)

                if cb:
                    cb.record_success()
                return response

            except Exception as e:
                errors.append((provider_name, str(e)))
                if cb:
                    cb.record_failure()
                logger.warning("Provider %s failed: %s", provider_name, e)
                continue

        if fallback_to_patterns and self.pattern_library:
            pattern_response = self.pattern_library.match(prompt)
            if pattern_response:
                return LLMResponse(
                    content=pattern_response,
                    provider="pattern_library",
                    model="offline",
                    cached=True,
                )

        error_summary = "; ".join(f"{p}: {e}" for p, e in errors)
        raise AllProvidersFailedError(
            f"No providers available. Errors: {error_summary}" if errors
            else "No providers configured or available"
        )

    def get_available_providers(self) -> List[str]:
        return [name for name, p in self.providers.items() if p.is_available()]

    def get_cost_report(self) -> Dict[str, Any]:
        """Get cost tracking statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "average_cost_per_request": self.total_cost / max(self.total_requests, 1),
        }

    def reset_stats(self):
        """Reset session statistics."""
        self.total_requests = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.session_stats = {}

    def get_status_report(self) -> Dict[str, Any]:
        return {
            "providers": {
                name: {
                    "available": self.provider_status.get(name, ProviderStatus(name=name, available=True)).available,
                    "circuit_breaker": self.circuit_breakers.get(name, CircuitBreaker()).state,
                }
                for name in self.providers
            },
            "cache_stats": self.cache.get_stats() if self.cache else None,
            "pattern_count": len(self.pattern_library.patterns) if self.pattern_library else 0,
            "strategy": self.strategy,
        }

    def refresh_status(self):
        for name, provider in self.providers.items():
            try:
                self.provider_status[name] = provider.health_check()
                cb = self.circuit_breakers.get(name)
                if cb:
                    if self.provider_status[name].available:
                        cb.record_success()
                    else:
                        cb.record_failure()
            except Exception as e:
                self.provider_status[name] = ProviderStatus(
                    name=name, available=False, error=str(e)
                )

    def get_health_report(self) -> Dict[str, Any]:
        """Get detailed health report for all providers."""
        self.refresh_status()
        
        report = {
            "providers": {},
            "summary": {
                "total": len(self.providers),
                "available": 0,
                "unavailable": 0,
            },
            "timestamp": time.time(),
        }
        
        for name, provider in self.providers.items():
            status = self.provider_status.get(name, ProviderStatus(name=name, available=False))
            
            report["providers"][name] = {
                "available": status.available,
                "latency_ms": status.latency_ms,
                "error": status.error,
                "circuit_breaker_state": self.circuit_breakers.get(name, CircuitBreaker()).state,
                "supports_streaming": provider.SUPPORTS_STREAMING,
                "supports_tools": provider.SUPPORTS_TOOLS,
                "supports_vision": provider.SUPPORTS_VISION,
                "model": getattr(provider, "model", "unknown"),
            }
            
            if status.available:
                report["summary"]["available"] += 1
            else:
                report["summary"]["unavailable"] += 1
        
        return report

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs):
        """Generate a streaming response from the best available provider."""
        messages: List[Message] = []
        if system_prompt:
            messages.append(Message(MessageRole.SYSTEM, system_prompt))
        messages.append(Message(MessageRole.USER, prompt))
        
        provider_order = self._get_provider_order(kwargs.get("task_type", "general"), kwargs)
        
        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            cb = self.circuit_breakers.get(provider_name)
            if cb and cb.is_open():
                continue
            
            if not provider.SUPPORTS_STREAMING:
                # Fall back to non-streaming
                try:
                    response = provider.generate(messages, **kwargs)
                    yield response.content
                    return
                except Exception:
                    continue
            
            try:
                yield from provider.generate_stream(messages, **kwargs)
                if cb:
                    cb.record_success()
                return
            except Exception as e:
                if cb:
                    cb.record_failure()
                logger.warning("Provider %s streaming failed: %s", provider_name, e)
                continue
        
        raise AllProvidersFailedError("No providers available for streaming")
