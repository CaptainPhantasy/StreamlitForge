"""LLM base classes and data types per PLANNING.md Section 4."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional
import time


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: MessageRole
    content: str


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    cached: bool = False
    cost_estimate: Optional[float] = None
    finish_reason: Optional[str] = None


@dataclass
class ProviderStatus:
    name: str
    available: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    model_count: int = 0
    last_check: Optional[str] = None


class LLMError(Exception):
    pass


class ProviderError(LLMError):
    pass


class AllProvidersFailedError(LLMError):
    pass


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    PROVIDER_NAME: str = "unknown"
    SUPPORTS_STREAMING: bool = False
    SUPPORTS_TOOLS: bool = False
    SUPPORTS_VISION: bool = False

    @abstractmethod
    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    def generate_stream(self, messages: List[Message], **kwargs):
        """Generate a streaming response. Override in providers that support streaming.
        
        Yields:
            str: Chunks of the response content
        """
        # Default implementation: fall back to non-streaming
        response = self.generate(messages, **kwargs)
        yield response.content

    def health_check(self) -> ProviderStatus:
        start = time.time()
        try:
            avail = self.is_available()
            return ProviderStatus(
                name=self.PROVIDER_NAME,
                available=avail,
                latency_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return ProviderStatus(name=self.PROVIDER_NAME, available=False, error=str(e))

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.PROVIDER_NAME,
            "model": getattr(self, "model", "unknown"),
            "streaming": self.SUPPORTS_STREAMING,
            "tools": self.SUPPORTS_TOOLS,
            "vision": self.SUPPORTS_VISION,
        }

    @property
    def name(self) -> str:
        return self.PROVIDER_NAME

    def estimate_cost(self, tokens: int) -> float:
        return 0.0


class CircuitBreaker:
    """Circuit breaker for provider failure handling."""

    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 60

    def __init__(self):
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time: Optional[float] = None

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.FAILURE_THRESHOLD:
            self.state = "OPEN"

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def is_open(self) -> bool:
        if self.state == "CLOSED":
            return False
        if self.state == "OPEN":
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.RECOVERY_TIMEOUT:
                self.state = "HALF_OPEN"
                return False
            return True
        return False
