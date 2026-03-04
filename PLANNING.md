# StreamlitForge - AI-Powered Streamlit Application Builder

## Executive Summary

A robust, vendor-agnostic CLI application that scaffolds, develops, and manages Streamlit applications with intelligent LLM assistance. Features deterministic port management, best-practice enforcement, and 10x robustness for offline/no-API scenarios.

---

## Core Philosophy

### 1. Vendor Agnosticism (Priority 1)
- Zero hard dependencies on any LLM provider
- Abstract interface pattern for all AI operations
- Provider ranking: Local > Free Tier > Paid
- Graceful degradation is not optional - it is mandatory

### 2. 10x Robustness for No-API Mode
- Full functionality without any API keys
- Local-first with cloud enhancement
- Every AI feature has a deterministic fallback
- Pattern library takes precedence over generated code when offline

### 3. Deterministic by Default
- Same inputs produce same outputs (port assignment, project structure, naming)
- Reproducible builds across machines and sessions
- No surprises, no conflicts

### 4. MCP-First Integration
- Leverage existing MCP tools before building new capabilities
- All MCP servers are optional dependencies with graceful fallback
- HTTP JSON-RPC 2.0 for loose coupling
- Cache MCP results locally for offline resilience

### 5. Continuous Learning
- Learn from every generation (success and failure)
- Episodic memory for problem-solving patterns
- Pattern crystallization for reusable solutions
- Usage analytics for improvement prioritization

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      StreamlitForge CLI                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Project    │  │    Port      │  │   Template   │          │
│  │   Manager    │  │   Manager    │  │    Engine    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    LLM Abstraction Layer                  │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │  │
│  │  │Ollama  │ │OpenAI  │ │Anthropic│ │Groq   │ │Google  │  │  │
│  │  │(Local) │ │        │ │        │ │(Free) │ │        │  │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Knowledge Systems                        │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │  Pattern   │  │   Web      │  │   Streamlit Docs   │  │  │
│  │  │  Library   │  │  Search    │  │   (Cached)         │  │  │
│  │  │  (Local)   │  │ (Grounding)│  │                    │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Offline Fallback Engine                  │  │
│  │  - Template-based generation                              │  │
│  │  - Pattern matching from learned library                  │  │
│  │  - Static component composition                           │  │
│  │  - Progressive enhancement when online                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   MCP Lab Integration Layer                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Hivemind   │  │   Omega     │  │  Context    │             │
│  │  (Orchest.) │  │ (Reasoning) │  │ Singularity │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Terminal   │  │  Safe-Ops   │  │  Supercache │             │
│  │  (Process)  │  │  (Refactor) │  │  (Memory)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Runner    │  │    ZAI      │  │    Web      │             │
│  │ (Validate)  │  │  (Vision)   │  │  (Search)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Specifications

### 1. Port Manager

**Purpose**: Deterministic, conflict-free port assignment

**Algorithm**:
```python
class PortManager:
    """
    Deterministic port assignment with registry fallback.
    
    Strategy:
    1. Calculate deterministic port from project path hash
    2. Check if port is available
    3. If conflict, use registry to find nearest available
    4. Register port with heartbeat for cleanup
    """
    
    BASE_PORT = 8501
    MAX_PORT = 8999
    REGISTRY_PATH = "~/.streamlitforge/port_registry.json"
    
    def get_port(self, project_path: str) -> int:
        # Primary: Deterministic hash
        deterministic_port = self._hash_path(project_path)
        
        if self._is_available(deterministic_port):
            self._register(deterministic_port, project_path)
            return deterministic_port
        
        # Fallback: Find nearest available
        for offset in range(1, 100):
            for port in [deterministic_port - offset, deterministic_port + offset]:
                if self.BASE_PORT <= port <= self.MAX_PORT and self._is_available(port):
                    self._register(port, project_path)
                    return port
        
        raise NoPortsAvailableError()
    
    def _hash_path(self, path: str) -> int:
        """Deterministic port from path hash."""
        import hashlib
        h = hashlib.sha256(os.path.abspath(path).encode()).hexdigest()
        return self.BASE_PORT + (int(h[:6], 16) % (self.MAX_PORT - self.BASE_PORT))
    
    def cleanup_stale(self, max_age_seconds: int = 3600):
        """Remove entries older than max_age without heartbeat."""
        pass
    
    def heartbeat(self, project_path: str):
        """Update timestamp to show project is active."""
        pass
```

**Registry Schema**:
```json
{
  "8501": {
    "project_path": "/Volumes/Storage/My_Whisper",
    "project_name": "My_Whisper",
    "pid": 12345,
    "last_heartbeat": "2026-03-03T18:30:00Z",
    "created": "2026-03-01T10:00:00Z"
  }
}
```

---

### 2. Project Manager

**Purpose**: Create, configure, and manage Streamlit projects

**Features**:
- Project scaffolding with best-practice structure
- `.streamlit/config.toml` auto-generation with assigned port
- Virtual environment creation
- Dependency management
- Git initialization with appropriate `.gitignore`

**Project Structure Template**:
```
{project_name}/
├── .streamlit/
│   └── config.toml          # Pre-configured with port
├── .venv/                    # Virtual environment
├── src/
│   ├── __init__.py
│   ├── app.py               # Main Streamlit app
│   ├── pages/               # Multi-page support
│   │   └── __init__.py
│   ├── components/          # Reusable components
│   │   └── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   └── config.py            # App configuration
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── assets/
│   └── logo.png             # Placeholder
├── data/                    # Sample data
│   └── .gitkeep
├── docs/
│   └── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── run.sh                   # Convenience script
└── README.md
```

**Generated Files**:

`.streamlit/config.toml`:
```toml
[server]
port = {ASSIGNED_PORT}
headless = true
runOnSave = true

[theme]
primaryColor = "#00D4FF"
backgroundColor = "#0D0D0D"
secondaryBackgroundColor = "#1A0A1F"
textColor = "#F8F8F8"

[client]
showErrorDetails = false
toolbarMode = "minimal"
```

`run.sh`:
```bash
#!/bin/bash
source .venv/bin/activate
streamlit run src/app.py
```

---

### 3. Template Engine

**Purpose**: Generate code from templates with AI enhancement

**Template Categories**:

1. **Page Templates**
   - Dashboard (metrics, charts, data tables)
   - Form (input validation, submission)
   - CRUD (create, read, update, delete)
   - Chat (LLM interface)
   - Analysis (data visualization)
   - Admin (settings, configuration)

2. **Component Templates**
   - Sidebar navigation
   - Data tables with export
   - Charts (line, bar, scatter, heatmap)
   - Forms with validation
   - File upload handlers
   - Authentication flows
   - Toast notifications
   - Progress indicators

3. **Integration Templates**
   - Database connections (SQLite, PostgreSQL, MongoDB)
   - API clients
   - LLM interfaces
   - Authentication providers
   - Cloud storage (S3, GCS)

**Template Format** (Jinja2):
```python
# component_data_table.py.j2
"""
{{ component_name }} - Data table component
Generated by StreamlitForge
"""
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any

def render_{{ component_name | snake_case }}(
    data: pd.DataFrame,
    title: str = "{{ default_title }}",
    {% if enable_search %}enable_search: bool = True,{% endif %}
    {% if enable_export %}enable_export: bool = True,{% endif %}
    {% if enable_pagination %}page_size: int = {{ default_page_size }},{% endif %}
) -> Optional[pd.DataFrame]:
    """
    Renders a data table with {{ features | join(', ') }}.
    
    Returns filtered dataframe if search is enabled and used.
    """
    st.subheader(title)
    
    {% if enable_search %}
    search = st.text_input("Search", key=f"search_{{ component_id }}")
    if search:
        # Search all string columns
        mask = data.astype(str).apply(lambda col: col.str.contains(search, case=False)).any(axis=1)
        data = data[mask]
    {% endif %}
    
    {% if enable_export %}
    col1, col2 = st.columns(2)
    with col1:
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button("Export CSV", csv, "{{ export_filename }}.csv", "text/csv")
    with col2:
        import json
        json_data = json.dumps(data.to_dict(orient='records'), indent=2)
        st.download_button("Export JSON", json_data, "{{ export_filename }}.json", "application/json")
    {% endif %}
    
    {% if enable_pagination %}
    # Pagination
    total_rows = len(data)
    total_pages = (total_rows + page_size - 1) // page_size
    page = st.number_input("Page", 1, total_pages, 1, key=f"page_{{ component_id }}")
    start_idx = (page - 1) * page_size
    data = data.iloc[start_idx:start_idx + page_size]
    {% endif %}
    
    st.dataframe(data, use_container_width=True)
    
    return data
```

---

### 4. LLM Abstraction Layer

**Purpose**: Vendor-agnostic AI integration with robust fallbacks

#### Provider Categories

**Tier 1: Local/Free (Highest Priority)**
| Provider | Type | Cost | Endpoint |
|----------|------|------|----------|
| Ollama | Local inference | Free | localhost:11434 |
| LM Studio | Local inference | Free | localhost:1234 |
| vLLM | Local inference | Free | localhost:8000 |
| LocalAI | OpenAI-compatible | Free | localhost:8080 |
| Jan | Desktop app | Free | localhost:1337 |

**Tier 2: Free/Freemium Cloud**
| Provider | Free Tier | Models | Notes |
|----------|-----------|--------|-------|
| Groq | Yes | Llama, Mixtral | Fastest inference |
| Google Gemini | Yes | Gemini 1.5/2.0 | 15 RPM free |
| Cohere | Yes | Command | Trial available |
| Together AI | Limited | Many | Pay-per-use |

**Tier 3: Paid Cloud**
| Provider | Models | Notes |
|----------|--------|-------|
| OpenAI | GPT-4, GPT-4o | Most reliable |
| Anthropic | Claude 3.5 | Best reasoning |
| Mistral | Mistral Large | European |
| DeepSeek | V3, R1 | Cost-effective |
| Replicate | Many | Model hosting |

**Tier 4: Aggregators**
| Provider | Description | Benefit |
|----------|-------------|---------|
| OpenRouter | Unified API for 100+ models | Single key, many models |
| Azure OpenAI | Enterprise OpenAI | Compliance, SLA |
| AWS Bedrock | Multi-provider | Enterprise, pay-per-use |

**Tier 7: Fallback**
| Provider | Type | When Used |
|----------|------|-----------|
| Pattern Library | Local templates | All APIs unavailable |
| Cached Responses | SQLite cache | Repeat queries |

#### Provider Priority Algorithm

```python
PROVIDER_PRIORITY = {
    # Tier 1: Local (always preferred when available)
    "local": {
        "ollama": {"weight": 100, "check": "http://localhost:11434/api/tags"},
        "lmstudio": {"weight": 99, "check": "http://localhost:1234/v1/models"},
        "vllm": {"weight": 98, "check": "http://localhost:8000/v1/models"},
        "localai": {"weight": 97, "check": "http://localhost:8080/v1/models"},
        "jan": {"weight": 96, "check": "http://localhost:1337/v1/models"},
    },
    # Tier 2: Free/Freemium
    "free_cloud": {
        "groq": {"weight": 90, "requires_key": True, "free_tier": True},
        "google": {"weight": 85, "requires_key": True, "free_tier": True},
        "cohere": {"weight": 80, "requires_key": True, "free_tier": True},
        "together": {"weight": 75, "requires_key": True, "free_tier": False},
    },
    # Tier 3: Curated Gateways (AI coding optimized, tested models)
    "curated": {
        "opencode_go": {
            "weight": 72, 
            "requires_key": True, 
            "cost": "$10/month",
            "models": ["glm-5", "kimi-k2.5", "minimax-m2.5"],
            "endpoints": "https://opencode.ai/zen/go/v1/"
        },
        "opencode_zen": {
            "weight": 68, 
            "requires_key": True, 
            "cost": "pay-as-you-go",
            "models": ["gpt-5.x", "claude-4.x", "gemini-3.x", "minimax-free", "big-pickle"],
            "endpoints": "https://opencode.ai/zen/v1/",
            "free_models": ["minimax-m2.5-free", "big-pickle", "gpt-5-nano"]
        },
    },
    # Tier 4: Aggregators (good middle ground)
    "aggregators": {
        "openrouter": {"weight": 70, "requires_key": True, "models": "100+"},
    },
    # Tier 5: Paid
    "paid": {
        "openai": {"weight": 60, "requires_key": True},
        "anthropic": {"weight": 55, "requires_key": True},
        "mistral": {"weight": 50, "requires_key": True},
        "deepseek": {"weight": 45, "requires_key": True},
        "replicate": {"weight": 40, "requires_key": True},
    },
    # Tier 6: Enterprise
    "enterprise": {
        "azure_openai": {"weight": 35, "requires_key": True, "requires_endpoint": True},
        "aws_bedrock": {"weight": 30, "requires_key": True, "requires_region": True},
    },
    # Tier 7: Fallback
    "fallback": {
        "cache": {"weight": 20, "always_available": True},
        "patterns": {"weight": 10, "always_available": True},
    }
}
```

#### Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
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

class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    # Provider metadata
    PROVIDER_NAME: str = "unknown"
    SUPPORTS_STREAMING: bool = True
    SUPPORTS_TOOLS: bool = False
    SUPPORTS_VISION: bool = False
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate response from messages."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response from messages."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API key, local server)."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderStatus:
        """Perform health check and return status."""
        pass
    
    @property
    def name(self) -> str:
        """Provider name."""
        return self.PROVIDER_NAME
    
    @property
    @abstractmethod
    def model(self) -> str:
        """Current model being used."""
        pass
    
    @property
    @abstractmethod
    def models(self) -> List[str]:
        """List available models."""
        pass
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token usage."""
        return 0.0  # Override in paid providers
```

#### Enhanced LLM Router

```python
class LLMRouter:
    """
    Intelligent router with provider selection, fallback, and optimization.
    
    Features:
    - Automatic provider discovery and ranking
    - Health monitoring with circuit breaker
    - Cost optimization (prefer free/cheap)
    - Latency-based routing
    - Response caching
    - Pattern library fallback
    """
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.provider_status: Dict[str, ProviderStatus] = {}
        self.cache = ResponseCache()
        self.pattern_library = PatternLibrary()
        
        # Circuit breaker state
        self.circuit_breaker: Dict[str, CircuitBreaker] = {}
        
        # Provider selection strategy
        self.strategy = config.get("router_strategy", "cost_optimized")  # cost_optimized, latency_optimized, quality_optimized
        
        self._init_all_providers()
        self._start_health_monitor()
    
    def _init_all_providers(self):
        """Initialize all possible providers."""
        
        # Local providers (no API key needed)
        local_providers = [
            ("ollama", OllamaProvider),
            ("lmstudio", LMStudioProvider),
            ("vllm", VLLMProvider),
            ("localai", LocalAIProvider),
            ("jan", JanProvider),
        ]
        
        # Curated gateway providers (AI coding optimized)
        curated_providers = [
            ("opencode_go", OpenCodeGoProvider),
            ("opencode_zen", OpenCodeZenProvider),
        ]
        
        # Cloud providers (need API key)
        cloud_providers = [
            ("groq", GroqProvider),
            ("google", GoogleProvider),
            ("cohere", CohereProvider),
            ("together", TogetherProvider),
            ("openrouter", OpenRouterProvider),
            ("openai", OpenAIProvider),
            ("anthropic", AnthropicProvider),
            ("mistral", MistralProvider),
            ("deepseek", DeepSeekProvider),
            ("replicate", ReplicateProvider),
        ]
        
        # Enterprise providers
        enterprise_providers = [
            ("azure_openai", AzureOpenAIProvider),
            ("aws_bedrock", AWSBedrockProvider),
        ]
        
        # Try to initialize each provider
        for name, provider_class in local_providers + cloud_providers + enterprise_providers:
            try:
                provider = provider_class(self.config)
                if provider.is_available():
                    self.providers[name] = provider
                    self.circuit_breaker[name] = CircuitBreaker()
                    logging.info(f"Initialized provider: {name}")
            except Exception as e:
                logging.debug(f"Provider {name} not available: {e}")
    
    def _start_health_monitor(self):
        """Start background health monitoring."""
        async def health_check_loop():
            while True:
                for name, provider in self.providers.items():
                    try:
                        status = await provider.health_check()
                        self.provider_status[name] = status
                        
                        # Update circuit breaker
                        if not status.available:
                            self.circuit_breaker[name].record_failure()
                        else:
                            self.circuit_breaker[name].record_success()
                    except Exception as e:
                        self.provider_status[name] = ProviderStatus(
                            name=name,
                            available=False,
                            error=str(e)
                        )
                
                await asyncio.sleep(60)  # Check every minute
        
        asyncio.create_task(health_check_loop())
    
    def select_provider(
        self,
        task_type: str = "general",
        prefer_speed: bool = False,
        prefer_quality: bool = False,
        max_cost: float = None,
        required_features: List[str] = None
    ) -> Optional[LLMProvider]:
        """
        Select best provider based on strategy and constraints.
        
        Args:
            task_type: Type of task (code, chat, analysis, etc.)
            prefer_speed: Prioritize low latency
            prefer_quality: Prioritize response quality
            max_cost: Maximum acceptable cost
            required_features: Required features (vision, tools, etc.)
        
        Returns:
            Best available provider or None
        """
        candidates = []
        
        for name, provider in self.providers.items():
            # Check circuit breaker
            if self.circuit_breaker[name].is_open():
                continue
            
            # Check availability
            status = self.provider_status.get(name)
            if status and not status.available:
                continue
            
            # Check required features
            if required_features:
                if "vision" in required_features and not provider.SUPPORTS_VISION:
                    continue
                if "tools" in required_features and not provider.SUPPORTS_TOOLS:
                    continue
            
            # Calculate score based on strategy
            score = self._calculate_provider_score(
                name, provider, task_type, 
                prefer_speed, prefer_quality, max_cost
            )
            
            candidates.append((score, name, provider))
        
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x[0], reverse=True)
        
        return candidates[0][2] if candidates else None
    
    def _calculate_provider_score(
        self,
        name: str,
        provider: LLMProvider,
        task_type: str,
        prefer_speed: bool,
        prefer_quality: bool,
        max_cost: float
    ) -> float:
        """Calculate provider score for selection."""
        
        # Base weight from priority
        base_weight = 50
        for tier in PROVIDER_PRIORITY.values():
            if name in tier:
                base_weight = tier[name]["weight"]
                break
        
        score = float(base_weight)
        
        # Adjust for strategy
        if self.strategy == "cost_optimized":
            cost = provider.estimate_cost(1000)
            if cost == 0:
                score += 20  # Bonus for free
            else:
                score -= cost * 10  # Penalize expensive
        
        elif self.strategy == "latency_optimized" or prefer_speed:
            status = self.provider_status.get(name)
            if status and status.latency_ms:
                # Lower latency = higher score
                score += max(0, 50 - status.latency_ms / 100)
        
        elif self.strategy == "quality_optimized" or prefer_quality:
            # Quality rankings (subjective but useful)
            quality_rankings = {
                "anthropic": 15,
                "openai": 12,
                "google": 10,
                "mistral": 8,
                "groq": 5,
            }
            score += quality_rankings.get(name, 0)
        
        # Task-specific adjustments
        if task_type == "code":
            code_bonuses = {"deepseek": 10, "openai": 8, "anthropic": 7}
            score += code_bonuses.get(name, 0)
        elif task_type == "analysis":
            analysis_bonuses = {"anthropic": 10, "openai": 8}
            score += analysis_bonuses.get(name, 0)
        
        # Cost constraint
        if max_cost is not None:
            cost = provider.estimate_cost(1000)
            if cost > max_cost:
                score -= 50  # Heavy penalty
        
        return score
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        task_type: str = "general",
        use_cache: bool = True,
        fallback_to_patterns: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response with intelligent routing and fallback.
        """
        
        # 1. Check cache
        if use_cache:
            cached = self.cache.get(prompt, system_prompt)
            if cached:
                return LLMResponse(
                    content=cached,
                    provider="cache",
                    model="cached",
                    cached=True
                )
        
        # 2. Build messages
        messages = []
        if system_prompt:
            messages.append(Message(MessageRole.SYSTEM, system_prompt))
        messages.append(Message(MessageRole.USER, prompt))
        
        # 3. Try providers with fallback
        errors = []
        
        # Get sorted providers
        provider_order = self._get_provider_order(task_type, kwargs)
        
        for provider_name in provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            # Check circuit breaker
            if self.circuit_breaker[provider_name].is_open():
                continue
            
            try:
                start_time = time.time()
                
                response = await provider.generate(
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                response.latency_ms = int((time.time() - start_time) * 1000)
                
                # Cache successful response
                if use_cache:
                    self.cache.set(prompt, system_prompt, response.content)
                
                # Record success
                self.circuit_breaker[provider_name].record_success()
                
                return response
                
            except Exception as e:
                errors.append((provider_name, str(e)))
                self.circuit_breaker[provider_name].record_failure()
                logging.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # 4. All providers failed, try pattern library
        if fallback_to_patterns:
            pattern_response = self.pattern_library.match(prompt)
            if pattern_response:
                return LLMResponse(
                    content=pattern_response,
                    provider="pattern_library",
                    model="offline",
                    cached=True
                )
        
        # 5. Complete failure
        error_summary = "; ".join(f"{p}: {e}" for p, e in errors)
        raise AllProvidersFailedError(f"No providers available. Errors: {error_summary}")
    
    def _get_provider_order(self, task_type: str, kwargs: dict) -> List[str]:
        """Get ordered list of providers to try."""
        
        prefer_speed = kwargs.get("prefer_speed", False)
        prefer_quality = kwargs.get("prefer_quality", False)
        max_cost = kwargs.get("max_cost", None)
        
        # Select best provider
        best = self.select_provider(
            task_type=task_type,
            prefer_speed=prefer_speed,
            prefer_quality=prefer_quality,
            max_cost=max_cost
        )
        
        if best:
            # Put best provider first, then others by priority
            ordered = [best.name]
            for name in self.providers:
                if name != best.name:
                    ordered.append(name)
            return ordered
        
        # Fallback to all providers by weight
        return list(self.providers.keys())
    
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response from best available provider."""
        
        messages = []
        if system_prompt:
            messages.append(Message(MessageRole.SYSTEM, system_prompt))
        messages.append(Message(MessageRole.USER, prompt))
        
        provider = self.select_provider()
        if not provider:
            raise NoProviderAvailableError()
        
        async for chunk in provider.stream(messages, temperature=temperature, **kwargs):
            yield chunk
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report."""
        return {
            "providers": {
                name: {
                    "available": status.available,
                    "latency_ms": status.latency_ms,
                    "error": status.error,
                    "model_count": status.model_count,
                    "circuit_breaker": str(self.circuit_breaker[name].state)
                }
                for name, status in self.provider_status.items()
            },
            "cache_stats": self.cache.get_stats(),
            "pattern_count": len(self.pattern_library.patterns),
            "strategy": self.strategy
        }
```

#### Provider Implementations

```python
class OllamaProvider(LLMProvider):
    """Local Ollama provider - highest priority."""
    
    PROVIDER_NAME = "ollama"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.base_url = config.get("ollama_url", "http://localhost:11434")
        self.model = config.get("ollama_model", "codellama:7b")
        self._models_cache: Optional[List[str]] = None
    
    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    async def health_check(self) -> ProviderStatus:
        start = time.time()
        try:
            response = await httpx.AsyncClient().get(
                f"{self.base_url}/api/tags", timeout=5.0
            )
            latency = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                return ProviderStatus(
                    name=self.PROVIDER_NAME,
                    available=True,
                    latency_ms=latency,
                    model_count=len(models),
                    last_check=datetime.now().isoformat()
                )
        except Exception as e:
            pass
        
        return ProviderStatus(
            name=self.PROVIDER_NAME,
            available=False,
            error="Connection failed"
        )
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.7),
                    "num_predict": kwargs.get("max_tokens", 4096)
                }
            },
            timeout=180.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["message"]["content"],
            provider="ollama",
            model=self.model,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=0.0
        )
    
    async def stream(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                    "stream": True,
                },
                timeout=180.0
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            yield data["message"].get("content", "")
    
    @property
    def models(self) -> List[str]:
        if self._models_cache is None:
            try:
                response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
                self._models_cache = [m["name"] for m in response.json().get("models", [])]
            except:
                self._models_cache = []
        return self._models_cache


class LMStudioProvider(LLMProvider):
    """LM Studio - OpenAI-compatible local server."""
    
    PROVIDER_NAME = "lmstudio"
    SUPPORTS_STREAMING = True
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.base_url = config.get("lmstudio_url", "http://localhost:1234/v1")
        self.model = config.get("lmstudio_model", "local-model")
    
    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/models", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        # OpenAI-compatible API
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096)
            },
            timeout=180.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="lmstudio",
            model=self.model,
            cost_estimate=0.0
        )
    
    async def stream(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True
                },
                timeout=180.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
    
    @property
    def models(self) -> List[str]:
        try:
            response = httpx.get(f"{self.base_url}/models", timeout=5.0)
            return [m["id"] for m in response.json().get("data", [])]
        except:
            return []


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter - Unified API for 100+ models.
    Supports OpenAI, Anthropic, Google, Meta, Mistral, and more.
    """
    
    PROVIDER_NAME = "openrouter"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True
    
    # Pricing per 1M tokens (approximate)
    MODEL_PRICING = {
        "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "openai/gpt-4o": {"input": 2.5, "output": 10.0},
        "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
        "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
        "google/gemini-pro-1.5": {"input": 2.5, "output": 10.0},
        "meta-llama/llama-3.1-70b-instruct": {"input": 0.52, "output": 0.75},
        "mistralai/mistral-large": {"input": 2.0, "output": 6.0},
        "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    }
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("openrouter_api_key") or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = config.get("openrouter_model", "openai/gpt-4o-mini")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://streamlitforge.dev",
                "X-Title": "StreamlitForge"
            },
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096)
            },
            timeout=120.0
        )
        
        data = response.json()
        
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="openrouter",
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=self.estimate_cost(tokens_used)
        )
    
    async def stream(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://streamlitforge.dev",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True
                },
                timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
    
    @property
    def models(self) -> List[str]:
        return list(self.MODEL_PRICING.keys())
    
    def estimate_cost(self, tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model, {"input": 1.0, "output": 3.0})
        # Assume 70% input, 30% output
        return (tokens * 0.7 * pricing["input"] + tokens * 0.3 * pricing["output"]) / 1_000_000


class OpenCodeGoProvider(LLMProvider):
    """
    OpenCode Go - $10/month subscription for curated open coding models.
    Models: GLM-5, Kimi K2.5, MiniMax M2.5
    Usage limits: 5hr ($12), weekly ($30), monthly ($60)
    Endpoint: https://opencode.ai/zen/go/v1/chat/completions
    """
    
    PROVIDER_NAME = "opencode_go"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = False
    SUPPORTS_VISION = False
    
    BASE_URL = "https://opencode.ai/zen/go/v1"
    MODELS = ["glm-5", "kimi-k2.5", "minimax-m2.5"]
    DEFAULT_MODEL = "minimax-m2.5"
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("opencode_go_api_key") or os.environ.get("OPENCODE_API_KEY")
        self.model = config.get("opencode_go_model", self.DEFAULT_MODEL)
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096)
            },
            timeout=120.0
        )
        
        data = response.json()
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="opencode_go",
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=0.0  # Flat $10/month subscription
        )
    
    async def stream(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True
                },
                timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
    
    @property
    def models(self) -> List[str]:
        return self.MODELS
    
    def estimate_cost(self, tokens: int) -> float:
        return 0.0  # Flat subscription model


class OpenCodeZenProvider(LLMProvider):
    """
    OpenCode Zen - Pay-as-you-go curated models with auto-reload.
    25+ curated and tested models including:
    - GPT-5.x, Claude 4.x, Gemini 3.x, Qwen3 Coder
    - Free models: MiniMax M2.5 Free, Big Pickle, GPT-5 Nano
    
    Endpoints:
    - OpenAI SDK: https://opencode.ai/zen/v1/responses
    - Anthropic SDK: https://opencode.ai/zen/v1/messages
    """
    
    PROVIDER_NAME = "opencode_zen"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = True
    
    BASE_URL_OPENAI = "https://opencode.ai/zen/v1"
    BASE_URL_ANTHROPIC = "https://opencode.ai/zen/v1"
    
    # Free models (no cost)
    FREE_MODELS = ["minimax-m2.5-free", "big-pickle", "gpt-5-nano"]
    
    # Pricing per 1M tokens (approximate, varies by model)
    MODEL_PRICING = {
        # Free models
        "minimax-m2.5-free": {"input": 0.0, "output": 0.0},
        "big-pickle": {"input": 0.0, "output": 0.0},
        "gpt-5-nano": {"input": 0.0, "output": 0.0},
        # Claude models
        "claude-opus-4-6": {"input": 5.0, "output": 25.0},
        "claude-sonnet-4-6": {"input": 1.5, "output": 7.5},
        "claude-haiku-4": {"input": 0.5, "output": 2.0},
        # GPT models
        "gpt-5-turbo": {"input": 2.0, "output": 8.0},
        "gpt-5": {"input": 5.0, "output": 15.0},
        # Gemini models
        "gemini-3-pro": {"input": 1.5, "output": 6.0},
        "gemini-3-flash": {"input": 0.3, "output": 1.0},
        # Other models
        "qwen3-coder": {"input": 0.5, "output": 1.5},
        "deepseek-r1": {"input": 0.5, "output": 2.0},
    }
    
    # Models that use Anthropic-style API
    ANTHROPIC_MODELS = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4"]
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("opencode_zen_api_key") or os.environ.get("OPENCODE_API_KEY")
        self.model = config.get("opencode_zen_model", "claude-sonnet-4-6")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    @property
    def is_anthropic_model(self) -> bool:
        return any(m in self.model for m in self.ANTHROPIC_MODELS)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        if self.is_anthropic_model:
            return await self._generate_anthropic(messages, **kwargs)
        return await self._generate_openai(messages, **kwargs)
    
    async def _generate_openai(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            f"{self.BASE_URL_OPENAI}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096)
            },
            timeout=120.0
        )
        
        data = response.json()
        usage = data.get("usage", {})
        tokens_used = usage.get("total_tokens", 0)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="opencode_zen",
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=self.estimate_cost(tokens_used)
        )
    
    async def _generate_anthropic(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        # Convert to Anthropic format
        anthropic_messages = []
        system_prompt = None
        
        for m in messages:
            if m.role.value == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({
                    "role": m.role.value,
                    "content": m.content
                })
        
        request_body = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 4096)
        }
        if system_prompt:
            request_body["system"] = system_prompt
        
        response = await httpx.AsyncClient().post(
            f"{self.BASE_URL_ANTHROPIC}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json=request_body,
            timeout=120.0
        )
        
        data = response.json()
        usage = data.get("usage", {})
        tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        
        # Extract content from Anthropic response format
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
        
        return LLMResponse(
            content=content,
            provider="opencode_zen",
            model=self.model,
            tokens_used=tokens_used,
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=self.estimate_cost(tokens_used)
        )
    
    async def stream(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        if self.is_anthropic_model:
            async for chunk in self._stream_anthropic(messages, **kwargs):
                yield chunk
        else:
            async for chunk in self._stream_openai(messages, **kwargs):
                yield chunk
    
    async def _stream_openai(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL_OPENAI}/responses",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True
                },
                timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        data = json.loads(line[6:])
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
    
    async def _stream_anthropic(self, messages: List[Message], **kwargs) -> AsyncIterator[str]:
        # Convert to Anthropic format
        anthropic_messages = []
        system_prompt = None
        
        for m in messages:
            if m.role.value == "system":
                system_prompt = m.content
            else:
                anthropic_messages.append({
                    "role": m.role.value,
                    "content": m.content
                })
        
        request_body = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True
        }
        if system_prompt:
            request_body["system"] = system_prompt
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL_ANTHROPIC}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=request_body,
                timeout=120.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
    
    @property
    def models(self) -> List[str]:
        return list(self.MODEL_PRICING.keys())
    
    def estimate_cost(self, tokens: int) -> float:
        pricing = self.MODEL_PRICING.get(self.model, {"input": 1.0, "output": 3.0})
        # Assume 70% input, 30% output
        return (tokens * 0.7 * pricing["input"] + tokens * 0.3 * pricing["output"]) / 1_000_000


class GroqProvider(LLMProvider):
    """Groq - Fastest inference, free tier available."""
    
    PROVIDER_NAME = "groq"
    SUPPORTS_STREAMING = True
    SUPPORTS_TOOLS = True
    SUPPORTS_VISION = False
    
    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = config.get("groq_model", "llama-3.3-70b-versatile")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
            },
            timeout=60.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="groq",
            model=self.model,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            latency_ms=int((time.time() - start) * 1000),
            cost_estimate=0.0  # Free tier
        )
    
    @property
    def models(self) -> List[str]:
        return self.AVAILABLE_MODELS


class MistralProvider(LLMProvider):
    """Mistral AI - European cloud provider."""
    
    PROVIDER_NAME = "mistral"
    SUPPORTS_STREAMING = True
    
    AVAILABLE_MODELS = [
        "mistral-large-latest",
        "mistral-medium-latest",
        "mistral-small-latest",
        "codestral-latest"
    ]
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("mistral_api_key") or os.environ.get("MISTRAL_API_KEY")
        self.base_url = "https://api.mistral.ai/v1"
        self.model = config.get("mistral_model", "mistral-large-latest")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
            },
            timeout=60.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="mistral",
            model=self.model,
            tokens_used=data.get("usage", {}).get("total_tokens")
        )
    
    @property
    def models(self) -> List[str]:
        return self.AVAILABLE_MODELS


class DeepSeekProvider(LLMProvider):
    """DeepSeek - Cost-effective, strong at code."""
    
    PROVIDER_NAME = "deepseek"
    SUPPORTS_STREAMING = True
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("deepseek_api_key") or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = config.get("deepseek_model", "deepseek-chat")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
            },
            timeout=120.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="deepseek",
            model=self.model,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            cost_estimate=self.estimate_cost(data.get("usage", {}).get("total_tokens", 0))
        )
    
    def estimate_cost(self, tokens: int) -> float:
        # DeepSeek is very cheap: ~$0.14/1M input, ~$0.28/1M output
        return tokens * 0.0002 / 1000
    
    @property
    def models(self) -> List[str]:
        return ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]


class CircuitBreaker:
    """
    Circuit breaker for provider failure handling.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject requests
    - HALF_OPEN: Testing if recovered
    """
    
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 60  # seconds
    
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
            # Check if recovery timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.RECOVERY_TIMEOUT:
                self.state = "HALF_OPEN"
                return False
            return True
        
        # HALF_OPEN - allow one request
        return False
```

#### Configuration

```yaml
# ~/.streamlitforge/config.yaml - LLM Configuration

llm:
  # Router strategy: cost_optimized, latency_optimized, quality_optimized
  strategy: cost_optimized
  
  # Task-specific model preferences
  task_models:
    code: deepseek/deepseek-coder
    chat: openai/gpt-4o-mini
    analysis: anthropic/claude-3.5-sonnet
  
  # Local providers
  ollama:
    url: http://localhost:11434
    model: codellama:7b
    timeout_seconds: 180
  
  lmstudio:
    url: http://localhost:1234/v1
    model: local-model
    timeout_seconds: 180
  
  vllm:
    url: http://localhost:8000/v1
    model: auto
    timeout_seconds: 180
  
  # Cloud providers (API keys from environment or secrets.toml)
  groq:
    api_key: ${GROQ_API_KEY}
    model: llama-3.3-70b-versatile
  
  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    model: openai/gpt-4o-mini
  
  # Curated Gateways (Tier 3)
  opencode_go:
    api_key: ${OPENCODE_API_KEY}
    model: minimax-m2.5
  
  opencode_zen:
    api_key: ${OPENCODE_API_KEY}
    model: claude-sonnet-4-6
  
  # Paid Cloud (Tier 5)
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o-mini
  
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
  
  google:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-2.0-flash
  
  mistral:
    api_key: ${MISTRAL_API_KEY}
    model: mistral-large-latest
  
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    model: deepseek-chat
  
  cohere:
    api_key: ${COHERE_API_KEY}
    model: command-r-plus
  
  together:
    api_key: ${TOGETHER_API_KEY}
    model: meta-llama/Llama-3-70b-chat-hf
  
  replicate:
    api_key: ${REPLICATE_API_KEY}
    model: meta/llama-2-70b-chat
  
  # Enterprise providers
  azure_openai:
    api_key: ${AZURE_OPENAI_API_KEY}
    endpoint: ${AZURE_OPENAI_ENDPOINT}
    deployment: gpt-4
    api_version: "2024-02-15-preview"
  
  aws_bedrock:
    access_key: ${AWS_ACCESS_KEY_ID}
    secret_key: ${AWS_SECRET_ACCESS_KEY}
    region: us-east-1
    model: anthropic.claude-3-sonnet-20240229-v1:0
  
  # Fallback settings
  fallback:
    use_cache: true
    cache_ttl_hours: 168
    use_pattern_library: true
    pattern_library_path: ~/.streamlitforge/patterns

  # Generation defaults
  generation:
    temperature: 0.3
    max_tokens: 4096
    timeout_seconds: 120
```
        
        # All providers failed, use pattern library
        if fallback_to_patterns:
            pattern_response = self.pattern_library.match(prompt)
            if pattern_response:
                return LLMResponse(
                    content=pattern_response,
                    provider="pattern_library",
                    model="offline",
                    cached=True
                )
        
        # Complete failure
        raise AllProvidersFailedError(f"No providers available. Last error: {last_error}")
```

**Provider Implementations**:

```python
class OllamaProvider(LLMProvider):
    """Local Ollama provider - highest priority."""
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.base_url = config.get("ollama_url", "http://localhost:11434")
        self.model = config.get("ollama_model", "codellama:7b")
    
    def is_available(self) -> bool:
        try:
            import httpx
            response = httpx.get(f"{self.base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        import httpx
        import time
        
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "stream": False,
            },
            timeout=120.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["message"]["content"],
            provider="ollama",
            model=self.model,
            latency_ms=int((time.time() - start) * 1000)
        )
    
    @property
    def name(self) -> str:
        return "ollama"


class GroqProvider(LLMProvider):
    """Groq provider - free tier, very fast."""
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.api_key = config.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        self.model = config.get("groq_model", "llama-3.1-70b-versatile")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        import httpx
        import time
        
        start = time.time()
        
        response = await httpx.AsyncClient().post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": m.role.value, "content": m.content} for m in messages],
                "temperature": kwargs.get("temperature", 0.7),
            },
            timeout=60.0
        )
        
        data = response.json()
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            provider="groq",
            model=self.model,
            tokens_used=data.get("usage", {}).get("total_tokens"),
            latency_ms=int((time.time() - start) * 1000)
        )
    
    @property
    def name(self) -> str:
        return "groq"


class PatternLibraryProvider(LLMProvider):
    """
    Offline fallback using pattern matching.
    This is the 10x robustness layer.
    """
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.library_path = Path(config.get("pattern_library_path", "~/.streamlitforge/patterns"))
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict[str, str]:
        """Load patterns from library."""
        patterns = {}
        pattern_files = [
            "streamlit_components.json",
            "data_handlers.json",
            "charts.json",
            "forms.json",
            "authentication.json",
            "layouts.json",
        ]
        
        for filename in pattern_files:
            filepath = self.library_path / filename
            if filepath.exists():
                with open(filepath) as f:
                    patterns.update(json.load(f))
        
        return patterns
    
    def is_available(self) -> bool:
        return bool(self.patterns)
    
    async def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        """Generate using pattern matching."""
        user_message = messages[-1].content if messages else ""
        
        # Find best matching pattern
        best_match = None
        best_score = 0
        
        for pattern_key, pattern_data in self.patterns.items():
            score = self._calculate_similarity(user_message, pattern_key)
            if score > best_score:
                best_score = score
                best_match = pattern_data
        
        if best_match and best_score > 0.5:
            # Template substitution
            content = self._substitute(best_match["template"], user_message)
            return LLMResponse(
                content=content,
                provider="pattern_library",
                model="offline",
                cached=True
            )
        
        # No good match, return generic response
        return LLMResponse(
            content=self._get_generic_response(user_message),
            provider="pattern_library",
            model="offline",
            cached=True
        )
    
    def _calculate_similarity(self, query: str, pattern_key: str) -> float:
        """Calculate similarity between query and pattern."""
        query_lower = query.lower()
        pattern_lower = pattern_key.lower()
        
        # Simple keyword matching
        query_words = set(query_lower.split())
        pattern_words = set(pattern_lower.split())
        
        intersection = query_words & pattern_words
        union = query_words | pattern_words
        
        return len(intersection) / len(union) if union else 0
    
    def _substitute(self, template: str, query: str) -> str:
        """Substitute placeholders in template."""
        # Extract component name from query
        import re
        words = re.findall(r'\b\w+\b', query.lower())
        component_name = "_".join(words[:3]) if words else "component"
        
        return template.replace("{{ component_name }}", component_name)
    
    def _get_generic_response(self, query: str) -> str:
        """Return generic Streamlit boilerplate."""
        return '''
# Generated by StreamlitForge (Offline Mode)
import streamlit as st

st.set_page_config(page_title="App", page_icon="🎯", layout="wide")

st.title("Welcome")

# Add your content here
st.write("This is a generated template. Customize as needed.")
'''
    
    @property
    def name(self) -> str:
        return "pattern_library"
    
    @property
    def model(self) -> str:
        return "offline"
```

---

### 5. Web Search & Grounding System

**Purpose**: Fetch latest Streamlit docs, examples, and best practices

**Grounding Sources**:
1. Streamlit official documentation (docs.streamlit.io)
2. Streamlit gallery examples
3. GitHub streamlit/streamlit repo
4. Stack Overflow (tagged: streamlit)
5. Python package index (PyPI) for versions

**Implementation**:
```python
class StreamlitKnowledgeBase:
    """
    Maintains up-to-date Streamlit knowledge via web grounding.
    Falls back to cached knowledge when offline.
    """
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.cache_path = Path(config.get("kb_cache_path", "~/.streamlitforge/knowledge"))
        self.cache_expiry = config.get("kb_cache_expiry_hours", 24)
        self._ensure_cache_dir()
    
    async def get_latest_features(self) -> Dict[str, Any]:
        """Get latest Streamlit features from docs."""
        cache_file = self.cache_path / "features.json"
        
        # Check cache
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            if self._is_cache_valid(cached):
                return cached["data"]
        
        # Fetch from web
        try:
            features = await self._fetch_features_from_docs()
            cache_file.write_text(json.dumps({
                "data": features,
                "fetched_at": datetime.now().isoformat()
            }))
            return features
        except Exception:
            # Return cached even if expired
            if cache_file.exists():
                return json.loads(cache_file.read_text())["data"]
            return self._get_builtin_features()
    
    async def search_examples(self, query: str) -> List[Dict]:
        """Search for Streamlit examples matching query."""
        # First search local cache
        local_results = self._search_local_examples(query)
        
        # Then search web if available
        try:
            web_results = await self._search_web_examples(query)
            # Merge and dedupe
            return self._merge_results(local_results, web_results)
        except:
            return local_results
    
    async def get_deprecations(self) -> List[Dict]:
        """Get list of deprecated Streamlit features."""
        # Check changelog for deprecations
        pass
    
    def _get_builtin_features(self) -> Dict[str, Any]:
        """Built-in knowledge as ultimate fallback."""
        return {
            "version": "1.41.0",
            "features": {
                "chat": ["st.chat_message", "st.chat_input"],
                "data": ["st.dataframe", "st.data_editor", "st.table"],
                "charts": ["st.line_chart", "st.bar_chart", "st.area_chart", "st.scatter_chart", "st.map"],
                "input": ["st.text_input", "st.text_area", "st.number_input", "st.slider", "st.selectbox", "st.multiselect", "st.checkbox", "st.radio", "st.date_input", "st.time_input", "st.file_uploader", "st.color_picker", "st.camera_input"],
                "layout": ["st.columns", "st.tabs", "st.expander", "st.sidebar", "st.container", "st.empty"],
                "media": ["st.image", "st.audio", "st.video"],
                "status": ["st.progress", "st.spinner", "st.status", "st.toast", "st.balloons", "st.snow"],
                "navigation": ["st.navigation", "st.Page", "st.switch_page"],
                "cache": ["st.cache_data", "st.cache_resource"],
                "session": ["st.session_state"],
                "theme": ["st.get_option", "st.set_option"],
            },
            "deprecations": [
                {"feature": "use_container_width", "replacement": "width='stretch' or width='content'", "removed_after": "2025-12-31"},
                {"feature": "@st.cache", "replacement": "@st.cache_data or @st.cache_resource", "removed_after": "2024-01-01"},
            ],
            "best_practices": [
                "Use st.set_page_config() as first command",
                "Use st.session_state for state persistence",
                "Use @st.cache_data for expensive computations",
                "Use st.columns for layouts, avoid nested columns",
                "Use st.toast for non-blocking notifications",
                "Use st.status for long-running operations",
            ]
        }
```

---

### 6. Pattern Library (10x Robustness Core)

**Purpose**: Learn and cache patterns for offline code generation

**Pattern Categories**:
- Component patterns (tables, forms, charts)
- Layout patterns (dashboards, multi-page)
- Integration patterns (databases, APIs)
- Style patterns (themes, CSS)
- Authentication patterns

**Pattern Storage**:
```json
{
  "pattern_id": "data_table_with_export",
  "name": "Data Table with Export",
  "triggers": ["table", "data", "export", "csv", "json", "filter"],
  "template": "...",
  "variables": {
    "component_name": {"type": "string", "default": "data_table"},
    "enable_search": {"type": "boolean", "default": true},
    "enable_export": {"type": "boolean", "default": true},
    "enable_pagination": {"type": "boolean", "default": false}
  },
  "examples": [
    {"input": "create a table with search and export", "output": "..."}
  ],
  "usage_count": 42,
  "last_used": "2026-03-03T18:30:00Z"
}
```

**Learning System**:
```python
class PatternLearner:
    """
    Learns patterns from successful code generations.
    Patterns are stored locally for offline use.
    """
    
    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.min_examples = 3  # Minimum examples before pattern is trusted
    
    def record_success(
        self,
        prompt: str,
        generated_code: str,
        user_modifications: Optional[str] = None
    ):
        """Record a successful generation for learning."""
        # Extract pattern from generated code
        pattern = self._extract_pattern(generated_code, user_modifications)
        
        # Find or create pattern entry
        existing = self._find_similar_pattern(prompt)
        if existing:
            existing["examples"].append({
                "input": prompt,
                "output": generated_code,
                "modified_output": user_modifications
            })
            existing["usage_count"] += 1
        else:
            self._create_pattern(prompt, pattern, generated_code)
    
    def _extract_pattern(self, code: str, modifications: Optional[str]) -> str:
        """Extract reusable pattern from code."""
        # Use AST to find parametric parts
        # Replace literals with placeholders
        # Identify variable parts
        pass
```

---

### 7. Configuration System

**Purpose**: Centralized configuration with sensible defaults

**Config File** (`~/.streamlitforge/config.yaml`):
```yaml
# StreamlitForge Configuration

# Project defaults
projects:
  base_path: ~/Projects/streamlit
  default_template: dashboard
  auto_git_init: true
  auto_venv: true

# Port management
ports:
  base_port: 8501
  max_port: 8999
  registry_path: ~/.streamlitforge/port_registry.json
  heartbeat_interval_seconds: 60
  stale_timeout_seconds: 3600

# LLM providers (in priority order)
llm:
  priority:
    - ollama
    - lmstudio
    - groq
    - openai
    - anthropic
    - google
    - cohere
  
  ollama:
    url: http://localhost:11434
    model: codellama:7b
    timeout_seconds: 120
  
  lmstudio:
    url: http://localhost:1234
    model: local-model
    timeout_seconds: 120
  
  groq:
    api_key: ${GROQ_API_KEY}
    model: llama-3.1-70b-versatile
  
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
  
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-5-sonnet-20241022
  
  google:
    api_key: ${GOOGLE_API_KEY}
    model: gemini-2.0-flash
  
  cohere:
    api_key: ${COHERE_API_KEY}
    model: command-r-plus
  
  # Fallback settings
  fallback:
    use_cache: true
    cache_ttl_hours: 168  # 1 week
    use_pattern_library: true
    pattern_library_path: ~/.streamlitforge/patterns

# Knowledge base
knowledge:
  cache_path: ~/.streamlitforge/knowledge
  cache_expiry_hours: 24
  sources:
    - url: https://docs.streamlit.io
      type: docs
    - url: https://github.com/streamlit/streamlit
      type: examples
    - url: https://discuss.streamlit.io
      type: community

# Code generation
generation:
  temperature: 0.3
  max_tokens: 4096
  include_comments: true
  include_type_hints: true
  python_version: "3.11"

# Templates
templates:
  custom_path: ~/.streamlitforge/templates
  builtin_priority: false  # Use custom templates first if available
```

---

## CLI Interface

### Commands

```bash
# Create new project
streamlitforge new <project_name> [options]
  --template, -t      Template name (dashboard, chat, crud, analysis, admin)
  --path, -p          Parent directory (default: ~/Projects/streamlit)
  --port              Specify port (default: auto-assign)
  --no-git            Skip git initialization
  --no-venv           Skip virtual environment creation
  --description, -d   Project description

# Generate component
streamlitforge generate <component_type> [options]
  --name, -n          Component name
  --output, -o        Output directory
  --inline            Print to stdout instead of file

# List projects
streamlitforge list
  --running           Show only running projects
  --all               Show all known projects

# Manage ports
streamlitforge ports
  --cleanup           Remove stale port assignments
  --release <port>    Release specific port
  --show <project>    Show port for project

# Run project
streamlitforge run <project_path>
  --port              Override port
  --detach, -d        Run in background

# Update knowledge base
streamlitforge update
  --force             Update even if cache is fresh
  --offline           Only update from local patterns

# Configure
streamlitforge config
  --set <key> <value> Set configuration value
  --get <key>         Get configuration value
  --init              Initialize configuration file

# Add to existing project
streamlitforge add <project_path> <component_type>
  --page              Add as a new page (multi-page app)
  --component         Add as reusable component
```

### Examples

```bash
# Create new dashboard project
streamlitforge new sales_dashboard --template dashboard

# Add a chart component to existing project
streamlitforge add ./sales_dashboard chart --name revenue_chart

# Generate a data table component
streamlitforge generate table --name users_table --output ./src/components/

# List all projects with their ports
streamlitforge list

# Run a project (uses assigned port automatically)
streamlitforge run ./sales_dashboard

# Update knowledge base with latest Streamlit features
streamlitforge update
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Port Manager with deterministic assignment
- [ ] Project scaffolding system
- [ ] Configuration management
- [ ] CLI framework setup

### Phase 2: LLM Integration (Week 2)
- [ ] LLM abstraction layer
- [ ] Provider implementations (Ollama, Groq, OpenAI, Anthropic)
- [ ] Response caching system
- [ ] Fallback chain implementation

### Phase 3: Knowledge & Patterns (Week 3)
- [ ] Web grounding system
- [ ] Streamlit docs scraper/cacher
- [ ] Pattern library foundation
- [ ] Built-in pattern library

### Phase 4: Template System (Week 4)
- [ ] Jinja2 template engine integration
- [ ] Built-in templates (dashboard, chat, crud, etc.)
- [ ] Component template library
- [ ] Template customization

### Phase 5: 10x Robustness (Week 5)
- [ ] Pattern learner implementation
- [ ] Enhanced offline mode
- [ ] Progressive enhancement system
- [ ] Error recovery mechanisms

### Phase 6: Polish & Testing (Week 6)
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Error message improvements
- [ ] Performance optimization

---

## File Structure

```
streamlitforge/
├── __init__.py
├── cli.py                      # CLI entry point
├── config.py                   # Configuration management
├── port_manager.py             # Port assignment
├── project_manager.py          # Project scaffolding
├── template_engine.py          # Template rendering
├── llm/
│   ├── __init__.py
│   ├── base.py                 # LLMProvider ABC
│   ├── router.py               # LLMRouter
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── ollama.py
│   │   ├── lmstudio.py
│   │   ├── groq.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── google.py
│   │   ├── cohere.py
│   │   └── pattern_library.py # Offline fallback
│   └── cache.py               # Response caching
├── knowledge/
│   ├── __init__.py
│   ├── base.py                 # KnowledgeBase ABC
│   ├── streamlit_kb.py         # Streamlit knowledge
│   ├── web_search.py           # Web grounding
│   └── local_patterns.py       # Pattern library
├── templates/
│   ├── projects/
│   │   ├── dashboard/
│   │   ├── chat/
│   │   ├── crud/
│   │   ├── analysis/
│   │   └── admin/
│   ├── components/
│   │   ├── table.py.j2
│   │   ├── chart.py.j2
│   │   ├── form.py.j2
│   │   └── ...
│   └── files/
│       ├── config.toml.j2
│       ├── requirements.txt.j2
│       ├── run.sh.j2
│       └── readme.md.j2
├── patterns/
│   ├── streamlit_components.json
│   ├── data_handlers.json
│   ├── charts.json
│   ├── forms.json
│   └── layouts.json
└── utils/
    ├── __init__.py
    ├── hashing.py
    ├── filesystem.py
    └── validation.py
```

---

## Testing Strategy

### Unit Tests
- Port assignment determinism
- Provider fallback chain
- Pattern matching accuracy
- Template rendering

### Integration Tests
- Full project creation flow
- LLM generation with each provider
- Offline mode functionality
- Cache invalidation

### E2E Tests
- Create, run, modify project
- Multi-project port management
- Update knowledge base
- Generate components

---

## Success Metrics

1. **Zero Port Conflicts**: Deterministic + registry prevents all conflicts
2. **100% Offline Capability**: Full functionality without any API
3. **Provider Agnostic**: Works with any LLM provider or none
4. **Knowledge Freshness**: Cached knowledge updated within 24 hours
5. **Pattern Accuracy**: >80% user acceptance of generated code
6. **Fast Generation**: <5 seconds for component generation (cached/offline)
7. **Easy Onboarding**: New project creation in <30 seconds

---

## Future Enhancements

1. **VS Code Extension**: GUI for project management
2. **Collaborative Patterns**: Share patterns between teams
3. **Component Marketplace**: Browse and install community components
4. **CI/CD Integration**: Auto-deploy to Streamlit Cloud
5. **Multi-framework Support**: Extend to Dash, Gradio, Panel
6. **Code Review Mode**: AI-powered code review for Streamlit apps
7. **Migration Assistant**: Upgrade deprecated Streamlit code

---

## 8. Interactive App Builder (Streamly-Inspired)

**Purpose**: Real-time chat interface for building Streamlit apps interactively

**Inspiration**: [Streamly](https://github.com/adielaine/streamly) - AI assistant for Streamlit development

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   StreamlitForge Chat UI                         │
├──────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Chat Mode     │  │   Build Mode    │  │   Expert Mode   │  │
│  │  (Q&A, Help)    │  │  (Gen Code)     │  │  (Senior Dev)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Conversation Manager                      │ │
│  │  - Session state persistence                               │ │
│  │  - Context window management                               │ │
│  │  - Code extraction & preview                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Code Preview Panel                        │ │
│  │  - Live syntax highlighting                                │ │
│  │  - One-click copy                                          │ │
│  │  - Preview in new tab                                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Modes

#### 1. Chat Mode (Help & Learning)
- Ask questions about Streamlit APIs
- Get code explanations
- Learn best practices
- Explore documentation

#### 2. Build Mode (Code Generation)
- Generate components from descriptions
- Create full pages/apps
- Add features to existing code
- Refactor and optimize

#### 3. Expert Mode (Senior Developer)
- Architectural guidance
- Performance optimization
- Security reviews
- Enterprise patterns

### Implementation

```python
class InteractiveBuilder:
    """
    Streamly-inspired interactive app builder.
    Supports real-time chat-based development.
    """
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.llm_router = LLMRouter(config)
        self.knowledge_base = StreamlitKnowledgeBase(config)
        self.code_preview = CodePreviewManager()
        self.persona = SeniorDeveloperPersona()
    
    def render_chat_interface(self):
        """Render the main chat interface."""
        st.set_page_config(
            page_title="StreamlitForge Builder",
            page_icon="🔨",
            layout="wide"
        )
        
        # Mode selector in sidebar
        mode = st.sidebar.radio(
            "Mode",
            ["💬 Chat", "🔧 Build", "🎓 Expert"],
            index=0
        )
        
        # Initialize session state
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.conversation_context = []
        
        # Render message history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                self._render_message(message)
        
        # Chat input
        if prompt := st.chat_input("Ask me about Streamlit..."):
            self._handle_input(prompt, mode)
    
    def _handle_input(self, prompt: str, mode: str):
        """Process user input and generate response."""
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response based on mode
        with st.chat_message("assistant"):
            if "Build" in mode:
                response = self._build_response(prompt)
            elif "Expert" in mode:
                response = self._expert_response(prompt)
            else:
                response = self._chat_response(prompt)
            
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
    
    def _build_response(self, prompt: str) -> str:
        """Generate code from natural language description."""
        system_prompt = """You are StreamlitForge Builder, an expert at generating 
        clean, idiomatic Streamlit code. Generate only the code needed, with brief 
        explanations. Follow Streamlit best practices."""
        
        # Get latest Streamlit knowledge for context
        features = await self.knowledge_base.get_latest_features()
        
        response = await self.llm_router.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temp for code
        )
        
        # Extract and cache any code blocks
        code_blocks = self._extract_code(response.content)
        if code_blocks:
            self.code_preview.cache_code(code_blocks)
        
        return response.content
    
    def _expert_response(self, prompt: str) -> str:
        """Generate expert-level guidance."""
        return self.persona.consult(prompt, self.llm_router)
```

---

## 9. Senior Developer Persona

**Purpose**: Provide 15+ years expertise for architectural decisions and code reviews

### System Prompt

```python
SENIOR_DEVELOPER_PROMPT = """
You are a Senior Streamlit Developer with 15+ years of experience in:
- Python web development (Flask, Django, FastAPI)
- Data visualization (Plotly, Altair, Matplotlib)
- Frontend development (React, Vue, modern CSS)
- Database design (SQL, NoSQL, ORMs)
- Cloud deployment (AWS, GCP, Azure)
- Performance optimization and scaling
- Security best practices

Your expertise in Streamlit specifically includes:
- All versions from 0.x through 1.x
- Session state management patterns
- Caching strategies for performance
- Multi-page app architecture
- Custom component development
- Enterprise deployment patterns
- Common pitfalls and anti-patterns

When answering:
1. Provide architectural context, not just code
2. Explain trade-offs and alternatives considered
3. Warn about potential issues before they occur
4. Suggest production-ready patterns over quick hacks
5. Reference specific Streamlit versions when relevant
6. Include error handling and edge cases

Tone: Professional, direct, and educational. You're a mentor, not just an answer bot.
"""
```

### Expertise Domains

```python
class SeniorDeveloperPersona:
    """Encapsulates senior developer expertise."""
    
    DOMAINS = {
        "architecture": [
            "Multi-page app structure",
            "State management patterns",
            "Component composition",
            "API integration patterns",
            "Authentication flows"
        ],
        "performance": [
            "Caching strategies",
            "Lazy loading",
            "Async operations",
            "Memory management",
            "Query optimization"
        ],
        "security": [
            "Input validation",
            "Secrets management",
            "Authentication/Authorization",
            "SQL injection prevention",
            "XSS protection"
        ],
        "deployment": [
            "Streamlit Cloud",
            "Docker containerization",
            "Kubernetes scaling",
            "CI/CD pipelines",
            "Environment configuration"
        ],
        "patterns": [
            "Repository pattern",
            "Factory pattern",
            "Observer pattern",
            "State machine",
            "Middleware chains"
        ]
    }
    
    def consult(self, question: str, llm: LLMRouter) -> str:
        """Provide expert consultation on a question."""
        # Detect domain from question
        domain = self._detect_domain(question)
        
        # Get relevant patterns
        patterns = self._get_patterns(domain)
        
        # Generate expert response
        system_prompt = SENIOR_DEVELOPER_PROMPT + f"\n\nFocus on: {domain}\nRelevant patterns: {patterns}"
        
        response = await llm.generate(
            prompt=question,
            system_prompt=system_prompt,
            temperature=0.5
        )
        
        return response.content
    
    def review_code(self, code: str, llm: LLMRouter) -> CodeReview:
        """Perform code review with senior developer perspective."""
        review_prompt = f"""
        Review this Streamlit code from a senior developer perspective:
        
        ```python
        {code}
        ```
        
        Provide:
        1. Overall assessment (1-10)
        2. Strengths
        3. Areas for improvement
        4. Security concerns
        5. Performance suggestions
        6. Best practice violations
        7. Refactoring recommendations
        """
        
        response = await llm.generate(
            prompt=review_prompt,
            system_prompt=SENIOR_DEVELOPER_PROMPT,
            temperature=0.3
        )
        
        return self._parse_review(response.content)
```

---

## 10. CLI-to-Enterprise Converter

**Purpose**: Transform prototype CLI tools into production-ready Streamlit apps

### Conversion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   CLI → Enterprise Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Input   │ -> │  Parse   │ -> │ Transform│ -> │ Generate │  │
│  │   CLI    │    │  Args    │    │  Logic   │    │   UI     │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Enhancement Layers                     │  │
│  │  - Input validation UI                                    │  │
│  │  - Progress indicators                                    │  │
│  │  - Error handling with user feedback                      │  │
│  │  - Results export (CSV, JSON, PDF)                        │  │
│  │  - Configuration persistence                              │  │
│  │  - User authentication (optional)                         │  │
│  │  - Audit logging                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class CLIToEnterpriseConverter:
    """
    Converts CLI applications to Streamlit enterprise apps.
    Preserves core logic while adding professional UI.
    """
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.llm = LLMRouter(config)
        self.templates = TemplateEngine(config)
    
    async def convert(
        self,
        cli_script: str,
        output_path: str,
        options: ConversionOptions
    ) -> ConversionResult:
        """
        Convert a CLI script to Streamlit app.
        
        Args:
            cli_script: Path to CLI Python script
            output_path: Where to create Streamlit app
            options: Conversion preferences
        
        Returns:
            ConversionResult with generated files and report
        """
        # 1. Parse CLI structure
        cli_info = await self._parse_cli(cli_script)
        
        # 2. Generate UI mapping
        ui_mapping = self._map_to_ui(cli_info)
        
        # 3. Create Streamlit app
        app_code = await self._generate_app(cli_info, ui_mapping, options)
        
        # 4. Add enterprise features
        if options.add_auth:
            app_code = self._add_authentication(app_code)
        if options.add_logging:
            app_code = self._add_audit_logging(app_code)
        if options.add_export:
            app_code = self._add_export_features(app_code)
        
        # 5. Write files
        self._write_project(output_path, app_code, cli_info)
        
        return ConversionResult(
            output_path=output_path,
            files_created=self._get_created_files(),
            cli_args_converted=len(cli_info.arguments),
            warnings=self._get_warnings()
        )
    
    async def _parse_cli(self, script_path: str) -> CLIInfo:
        """Parse CLI script to extract structure."""
        with open(script_path) as f:
            code = f.read()
        
        prompt = f"""
        Analyze this CLI script and extract:
        1. All arguments (positional and optional)
        2. Input types and validation
        3. Main processing logic
        4. Output format
        5. Error handling patterns
        
        Script:
        ```python
        {code}
        ```
        
        Return as JSON with keys: arguments, inputs, processing, outputs, errors
        """
        
        response = await self.llm.generate(prompt, temperature=0.1)
        return CLIInfo.from_json(response.content)
    
    def _map_to_ui(self, cli_info: CLIInfo) -> UIMapping:
        """Map CLI arguments to Streamlit widgets."""
        mapping = {}
        
        for arg in cli_info.arguments:
            if arg.type == bool:
                mapping[arg.name] = WidgetMapping(
                    widget="st.checkbox",
                    params={"label": arg.help or arg.name}
                )
            elif arg.choices:
                mapping[arg.name] = WidgetMapping(
                    widget="st.selectbox",
                    params={
                        "label": arg.help or arg.name,
                        "options": arg.choices
                    }
                )
            elif arg.type == int:
                mapping[arg.name] = WidgetMapping(
                    widget="st.number_input",
                    params={
                        "label": arg.help or arg.name,
                        "step": 1,
                        "value": arg.default
                    }
                )
            elif arg.type == float:
                mapping[arg.name] = WidgetMapping(
                    widget="st.number_input",
                    params={
                        "label": arg.help or arg.name,
                        "step": 0.01,
                        "value": arg.default
                    }
                )
            elif arg.is_file:
                mapping[arg.name] = WidgetMapping(
                    widget="st.file_uploader",
                    params={"label": arg.help or arg.name}
                )
            else:
                mapping[arg.name] = WidgetMapping(
                    widget="st.text_input",
                    params={"label": arg.help or arg.name}
                )
        
        return UIMapping(mapping)
```

### Conversion Options

```python
@dataclass
class ConversionOptions:
    """Options for CLI to Enterprise conversion."""
    
    # UI Options
    add_sidebar: bool = True
    add_progress_bar: bool = True
    add_export: bool = True
    add_dark_mode: bool = True
    
    # Enterprise Options
    add_auth: bool = False
    auth_provider: str = "streamlit"  # streamlit, auth0, okta
    add_logging: bool = True
    add_metrics: bool = False
    
    # Output Options
    export_formats: List[str] = field(default_factory=lambda: ["csv", "json"])
    add_visualizations: bool = True
    
    # Quality Options
    add_error_handling: bool = True
    add_input_validation: bool = True
    add_tooltips: bool = True
```

---

## 11. Auto-Updating Streamlit Knowledge System

**Purpose**: Keep knowledge current without manual intervention

### Knowledge Sources

```python
class AutoUpdatingKnowledgeBase:
    """
    Automatically updates Streamlit knowledge from multiple sources.
    Works offline with cached data, updates when online.
    """
    
    SOURCES = {
        "official_docs": {
            "url": "https://docs.streamlit.io",
            "parser": "streamlit_docs_parser",
            "priority": 1,
            "cache_hours": 24
        },
        "changelog": {
            "url": "https://docs.streamlit.io/develop/quick-reference/changelog",
            "parser": "changelog_parser",
            "priority": 1,
            "cache_hours": 12
        },
        "github_repo": {
            "url": "https://github.com/streamlit/streamlit",
            "parser": "github_parser",
            "priority": 2,
            "cache_hours": 24
        },
        "discuss_forum": {
            "url": "https://discuss.streamlit.io",
            "parser": "discourse_parser",
            "priority": 3,
            "cache_hours": 48
        },
        "stackoverflow": {
            "url": "https://stackoverflow.com/questions/tagged/streamlit",
            "parser": "so_parser",
            "priority": 3,
            "cache_hours": 72
        },
        "pypi": {
            "url": "https://pypi.org/pypi/streamlit/json",
            "parser": "pypi_parser",
            "priority": 1,
            "cache_hours": 6
        }
    }
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.cache_path = Path(config.get("kb_cache_path", "~/.streamlitforge/knowledge"))
        self.update_interval = config.get("kb_update_interval_hours", 24)
        self._ensure_cache_dir()
        self._start_background_updater()
    
    def _start_background_updater(self):
        """Start background thread for knowledge updates."""
        import threading
        
        def update_loop():
            while True:
                try:
                    self.update_if_stale()
                except Exception as e:
                    logging.error(f"Knowledge update failed: {e}")
                time.sleep(self.update_interval * 3600)
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
    
    async def get_current_version(self) -> str:
        """Get current Streamlit version."""
        # Try PyPI first (most accurate)
        try:
            response = await httpx.AsyncClient().get(
                "https://pypi.org/pypi/streamlit/json",
                timeout=10.0
            )
            return response.json()["info"]["version"]
        except:
            # Fallback to cached
            cached = self._get_cached_version()
            if cached:
                return cached
            # Ultimate fallback
            return "1.41.0"
    
    async def get_deprecations(self) -> List[DeprecationInfo]:
        """Get list of deprecated features."""
        cache_file = self.cache_path / "deprecations.json"
        
        if self._is_cache_valid(cache_file, hours=24):
            return self._load_cache(cache_file)
        
        # Scrape changelog for deprecations
        deprecations = await self._scrape_deprecations()
        self._save_cache(cache_file, deprecations)
        
        return deprecations
    
    async def get_new_features(self, since_version: str) -> List[FeatureInfo]:
        """Get features added since specified version."""
        cache_file = self.cache_path / f"features_since_{since_version}.json"
        
        if self._is_cache_valid(cache_file, hours=48):
            return self._load_cache(cache_file)
        
        # Parse changelog entries
        features = await self._parse_changelog_since(since_version)
        self._save_cache(cache_file, features)
        
        return features
    
    async def search_examples(self, query: str) -> List[CodeExample]:
        """Search for code examples matching query."""
        # Search local cache first
        local = self._search_local_examples(query)
        
        # Try web search if online
        if await self._is_online():
            try:
                web = await self._search_web_examples(query)
                return self._merge_and_rank(local, web)
            except:
                pass
        
        return local
```

### Knowledge Update Schedule

```python
UPDATE_SCHEDULE = {
    "critical": {  # Updates every 6 hours
        "version_info",
        "security_advisories",
        "breaking_changes"
    },
    "important": {  # Updates every 24 hours
        "new_features",
        "deprecations",
        "best_practices"
    },
    "normal": {  # Updates every 48-72 hours
        "examples",
        "tutorials",
        "community_qa"
    }
}
```

---

## 12. Deployment & Sharing Integration

**Purpose**: One-stop deployment to multiple platforms

### Supported Platforms

```python
class DeploymentManager:
    """
    Deploy Streamlit apps to various platforms.
    Handles configuration, secrets, and monitoring.
    """
    
    PLATFORMS = {
        "streamlit_cloud": {
            "name": "Streamlit Community Cloud",
            "free_tier": True,
            "requires": ["github_repo"],
            "config_file": ".streamlit/config.toml"
        },
        "docker": {
            "name": "Docker Container",
            "free_tier": True,
            "requires": ["dockerfile"],
            "config_file": "Dockerfile"
        },
        "kubernetes": {
            "name": "Kubernetes Cluster",
            "free_tier": False,
            "requires": ["k8s_manifests"],
            "config_file": "k8s/deployment.yaml"
        },
        "aws": {
            "name": "AWS (ECS/Fargate)",
            "free_tier": False,
            "requires": ["aws_credentials"],
            "config_file": "aws/task-definition.json"
        },
        "gcp": {
            "name": "Google Cloud Run",
            "free_tier": True,  # Has free tier
            "requires": ["gcp_credentials"],
            "config_file": "gcp/service.yaml"
        },
        "azure": {
            "name": "Azure Container Instances",
            "free_tier": False,
            "requires": ["azure_credentials"],
            "config_file": "azure/container.yaml"
        },
        "heroku": {
            "name": "Heroku",
            "free_tier": False,
            "requires": ["heroku_app"],
            "config_file": "Procfile"
        },
        "render": {
            "name": "Render",
            "free_tier": True,
            "requires": ["render_account"],
            "config_file": "render.yaml"
        },
        "railway": {
            "name": "Railway",
            "free_tier": True,
            "requires": ["railway_account"],
            "config_file": "railway.toml"
        }
    }
    
    async def deploy(
        self,
        project_path: str,
        platform: str,
        options: DeploymentOptions
    ) -> DeploymentResult:
        """Deploy project to specified platform."""
        
        if platform == "streamlit_cloud":
            return await self._deploy_streamlit_cloud(project_path, options)
        elif platform == "docker":
            return await self._deploy_docker(project_path, options)
        elif platform == "gcp":
            return await self._deploy_gcp(project_path, options)
        # ... other platforms
    
    async def _deploy_streamlit_cloud(
        self,
        project_path: str,
        options: DeploymentOptions
    ) -> DeploymentResult:
        """Deploy to Streamlit Community Cloud."""
        
        # 1. Validate project structure
        self._validate_for_streamlit_cloud(project_path)
        
        # 2. Check/create GitHub repo
        repo_url = await self._ensure_github_repo(project_path, options)
        
        # 3. Generate deployment config
        config = self._generate_streamlit_cloud_config(project_path, options)
        
        # 4. Push to GitHub
        await self._push_to_github(project_path, repo_url, config)
        
        # 5. Create Streamlit Cloud app (via browser automation or API)
        app_url = await self._create_streamlit_app(repo_url, options)
        
        return DeploymentResult(
            success=True,
            platform="streamlit_cloud",
            url=app_url,
            repo_url=repo_url
        )
```

### Deployment Configuration Generator

```python
class DeploymentConfigGenerator:
    """Generate deployment configs for various platforms."""
    
    def generate_dockerfile(self, project_info: ProjectInfo) -> str:
        """Generate optimized Dockerfile for Streamlit app."""
        return f'''# Generated by StreamlitForge
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE {project_info.port}

# Health check
HEALTHCHECK CMD curl --fail http://localhost:{project_info.port}/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port={project_info.port}", "--server.address=0.0.0.0"]
'''
    
    def generate_docker_compose(self, project_info: ProjectInfo) -> str:
        """Generate docker-compose.yml for local development."""
        return f'''# Generated by StreamlitForge
version: '3.8'

services:
  app:
    build: .
    ports:
      - "{project_info.port}:{project_info.port}"
    environment:
      - STREAMLIT_SERVER_PORT={project_info.port}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    
  # Optional: Add database
  # db:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_DB: {project_info.name}
  #     POSTGRES_PASSWORD: secret
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
'''
    
    def generate_render_yaml(self, project_info: ProjectInfo) -> str:
        """Generate render.yaml for Render deployment."""
        return f'''# Generated by StreamlitForge
services:
  - type: web
    name: {project_info.name}
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run src/app.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
'''
```

### Sharing Features

```python
class SharingManager:
    """Share Streamlit apps via various channels."""
    
    async def create_share_link(
        self,
        project_path: str,
        share_type: str,  # "embed", "preview", "public"
        expiry: Optional[datetime] = None
    ) -> ShareLink:
        """Create a shareable link for the app."""
        pass
    
    async def embed_code(
        self,
        app_url: str,
        options: EmbedOptions
    ) -> str:
        """Generate embed code for the app."""
        height = options.height or 800
        return f'''<iframe
    src="{app_url}?embed=true"
    width="100%"
    height="{height}"
    style="border: none;">
</iframe>'''
    
    async def export_as_html(
        self,
        project_path: str,
        output_path: str
    ) -> str:
        """Export app as static HTML (limited functionality)."""
        pass
```

---

## 13. Floyd Labs MCP Integration

**Purpose**: Leverage Floyd Labs MCP servers for enhanced capabilities

### Integration Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   StreamlitForge + MCP Lab                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                 MCP Client (HTTP JSON-RPC 2.0)               │ │
│  │  Endpoint: http://localhost:8108/mcp                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│         ┌────────────────────┼────────────────────┐              │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │floyd-       │    │floyd-       │    │context-     │          │
│  │supercache   │    │devtools     │    │singularity  │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │floyd-       │    │novel-       │    │pattern-     │          │
│  │safe-ops     │    │concepts     │    │crystallizer │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### MCP Client Implementation

```python
class MCPLabClient:
    """
    HTTP JSON-RPC 2.0 client for Floyd Labs MCP servers.
    Provides unified access to MCP tool ecosystem.
    """
    
    def __init__(self, endpoint: str = "http://localhost:8108/mcp"):
        self.endpoint = endpoint
        self.request_id = 0
        self.timeout = 30.0
    
    async def call_tool(
        self,
        server: str,
        tool: str,
        arguments: dict
    ) -> dict:
        """
        Call an MCP tool via JSON-RPC 2.0.
        
        Args:
            server: MCP server name (e.g., "floyd-supercache")
            tool: Tool name (e.g., "cache_store")
            arguments: Tool arguments
        
        Returns:
            Tool result
        """
        self.request_id += 1
        
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": f"mcp_{server}_{tool}",
            "params": arguments
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
        
        if "error" in result:
            raise MCPToolError(result["error"])
        
        return result.get("result", {})


class StreamlitForgeMCPIntegration:
    """
    Integrates StreamlitForge with Floyd Labs MCP ecosystem.
    """
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.mcp = MCPLabClient(config.get("mcp_endpoint", "http://localhost:8108/mcp"))
        self._init_integrations()
    
    def _init_integrations(self):
        """Initialize MCP-based integrations."""
        self.supercache = SupercacheIntegration(self.mcp)
        self.devtools = DevToolsIntegration(self.mcp)
        self.context = ContextIntegration(self.mcp)
        self.safe_ops = SafeOpsIntegration(self.mcp)
        self.patterns = PatternIntegration(self.mcp)
    
    async def store_pattern(
        self,
        name: str,
        pattern: dict,
        tags: list[str]
    ) -> str:
        """Store a learned pattern in SUPERCACHE vault."""
        return await self.supercache.store_pattern(name, pattern, tags)
    
    async def retrieve_pattern(self, query: str) -> list[dict]:
        """Retrieve similar patterns from cache."""
        return await self.supercache.search(query)
    
    async def safe_refactor(
        self,
        operations: list[dict],
        verify_command: str
    ) -> dict:
        """Perform safe refactoring with automatic rollback."""
        return await self.safe_ops.refactor(operations, verify_command)
    
    async def index_codebase(self, root_path: str) -> dict:
        """Index codebase for semantic search."""
        return await self.context.ingest(root_path)
```

### Supercache Integration

```python
class SupercacheIntegration:
    """
    Integration with floyd-supercache for pattern storage.
    
    Tiers:
    - project: Session-scoped, TTL 1 hour
    - reasoning: Persistent chains for learning
    - vault: Long-term archive for patterns
    """
    
    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp
    
    async def store_pattern(
        self,
        name: str,
        pattern: dict,
        tags: list[str],
        tier: str = "vault"
    ) -> str:
        """Store a pattern in cache."""
        result = await self.mcp.call_tool(
            server="floyd-supercache",
            tool="cache_store_pattern",
            arguments={
                "name": name,
                "pattern": pattern,
                "tags": tags,
                "category": "streamlit"
            }
        )
        return result.get("key")
    
    async def search(self, query: str, tier: str = "all") -> list[dict]:
        """Search cached patterns."""
        result = await self.mcp.call_tool(
            server="floyd-supercache",
            tool="cache_search",
            arguments={
                "query": query,
                "tier": tier,
                "limit": 20
            }
        )
        return result.get("results", [])
    
    async def store_reasoning(
        self,
        context: str,
        reasoning: str,
        conclusion: str
    ) -> str:
        """Store reasoning chain for future reference."""
        result = await self.mcp.call_tool(
            server="floyd-supercache",
            tool="cache_store_reasoning",
            arguments={
                "context": context,
                "reasoning": reasoning,
                "conclusion": conclusion,
                "metadata": {"domain": "streamlit"}
            }
        )
        return result.get("id")
```

### Safe Operations Integration

```python
class SafeOpsIntegration:
    """
    Integration with floyd-safe-ops for safe code modifications.
    """
    
    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp
    
    async def refactor(
        self,
        operations: list[dict],
        verify_command: str,
        git_commit: bool = False
    ) -> dict:
        """
        Perform safe refactoring with automatic rollback.
        
        Args:
            operations: List of edit operations
            verify_command: Command to verify changes
            git_commit: Whether to commit if successful
        
        Returns:
            Refactoring result
        """
        return await self.mcp.call_tool(
            server="floyd-safe-ops",
            tool="safe_refactor",
            arguments={
                "operations": operations,
                "verifyCommand": verify_command,
                "gitCommit": git_commit
            }
        )
    
    async def simulate_impact(
        self,
        operations: list[dict],
        project_path: str
    ) -> dict:
        """Simulate impact of changes before applying."""
        return await self.mcp.call_tool(
            server="floyd-safe-ops",
            tool="impact_simulate",
            arguments={
                "operations": operations,
                "resolvedProjectPath": project_path
            }
        )
    
    async def verify(
        self,
        strategy: str,
        command: str = None,
        file: str = None
    ) -> dict:
        """Verify changes work correctly."""
        return await self.mcp.call_tool(
            server="floyd-safe-ops",
            tool="verify",
            arguments={
                "strategy": strategy,
                "command": command,
                "file": file
            }
        )
```

### DevTools Integration

```python
class DevToolsIntegration:
    """
    Integration with floyd-devtools for code analysis.
    """
    
    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp
    
    async def analyze_dependencies(
        self,
        project_path: str
    ) -> dict:
        """Analyze project dependencies for cycles."""
        return await self.mcp.call_tool(
            server="floyd-devtools",
            tool="dependency_analyzer",
            arguments={
                "action": "analyze",
                "project_path": project_path,
                "language": "python"
            }
        )
    
    async def generate_tests(
        self,
        source_code: str,
        framework: str = "pytest"
    ) -> str:
        """Generate tests for source code."""
        result = await self.mcp.call_tool(
            server="floyd-devtools",
            tool="test_generator",
            arguments={
                "action": "generate",
                "source_code": source_code,
                "framework": framework,
                "include_edge_cases": True
            }
        )
        return result.get("tests", "")
    
    async def analyze_typescript(
        self,
        project_path: str,
        action: str = "find_type_mismatches"
    ) -> dict:
        """Analyze TypeScript for type issues."""
        return await self.mcp.call_tool(
            server="floyd-devtools",
            tool="typescript_semantic_analyzer",
            arguments={
                "action": action,
                "project_path": project_path
            }
        )
```

### Pattern Crystallizer Integration

```python
class PatternIntegration:
    """
    Integration with pattern-crystallizer for learning patterns.
    """
    
    def __init__(self, mcp: MCPLabClient):
        self.mcp = mcp
    
    async def detect_and_crystallize(
        self,
        code: str,
        context: str,
        tags: list[str]
    ) -> dict:
        """Auto-detect patterns in code and crystallize."""
        return await self.mcp.call_tool(
            server="pattern-crystallizer",
            tool="detect_and_crystallize",
            arguments={
                "code": code,
                "context": context,
                "language": "python",
                "tags": tags,
                "auto_crystallize": True
            }
        )
    
    async def adapt_pattern(
        self,
        query: str,
        current_context: str
    ) -> list[dict]:
        """Find and adapt existing patterns to current context."""
        result = await self.mcp.call_tool(
            server="pattern-crystallizer",
            tool="adapt_pattern",
            arguments={
                "query": query,
                "current_context": current_context,
                "max_results": 5
            }
        )
        return result.get("patterns", [])
    
    async def store_episode(
        self,
        trigger: str,
        reasoning: str,
        solution: str,
        outcome: str
    ) -> str:
        """Store a problem-solving episode."""
        result = await self.mcp.call_tool(
            server="pattern-crystallizer",
            tool="store_episode",
            arguments={
                "trigger": trigger,
                "reasoning": reasoning,
                "solution": solution,
                "outcome": outcome
            }
        )
        return result.get("id")
```

---

## 14. API Key Configuration Entry Point

**Purpose**: Centralized, secure API key management

### Configuration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Key Configuration                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Priority Order:                                                │
│  1. Environment Variables (highest priority)                    │
│  2. .env file in project directory                              │
│  3. ~/.streamlitforge/secrets.toml                              │
│  4. ~/.streamlitforge/config.yaml (encrypted)                   │
│  5. Interactive prompt (lowest priority)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class APIKeyManager:
    """
    Centralized API key management with secure storage.
    """
    
    SUPPORTED_PROVIDERS = [
        "openai",
        "anthropic",
        "groq",
        "google",
        "cohere"
    ]
    
    ENV_MAPPINGS = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "google": "GOOGLE_API_KEY",
        "cohere": "COHERE_API_KEY"
    }
    
    def __init__(self, config: "StreamlitForgeConfig"):
        self.config = config
        self.secrets_path = Path.home() / ".streamlitforge" / "secrets.toml"
        self._keys: dict[str, str] = {}
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from all sources."""
        for provider in self.SUPPORTED_PROVIDERS:
            key = self._get_key(provider)
            if key:
                self._keys[provider] = key
    
    def _get_key(self, provider: str) -> str | None:
        """Get API key for provider from all sources."""
        env_var = self.ENV_MAPPINGS.get(provider)
        
        # 1. Environment variable (highest priority)
        key = os.environ.get(env_var)
        if key:
            return key
        
        # 2. .env file in project directory
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            key = self._read_env_file(env_file, env_var)
            if key:
                return key
        
        # 3. secrets.toml
        if self.secrets_path.exists():
            key = self._read_secrets_toml(provider)
            if key:
                return key
        
        # 4. config.yaml (encrypted)
        key = self.config.get(f"llm.{provider}.api_key")
        if key and not key.startswith("${"):
            return key
        
        return None
    
    def _read_env_file(self, path: Path, var: str) -> str | None:
        """Read variable from .env file."""
        import re
        content = path.read_text()
        match = re.search(rf"^{var}=(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip().strip('"').strip("'")
        return None
    
    def _read_secrets_toml(self, provider: str) -> str | None:
        """Read key from secrets.toml."""
        try:
            import tomllib
            with open(self.secrets_path, "rb") as f:
                secrets = tomllib.load(f)
            return secrets.get(f"{provider}_api_key")
        except Exception:
            return None
    
    def get(self, provider: str) -> str | None:
        """Get API key for provider."""
        return self._keys.get(provider)
    
    def has(self, provider: str) -> bool:
        """Check if API key exists for provider."""
        return provider in self._keys
    
    def set(self, provider: str, key: str, persist: bool = True):
        """
        Set API key for provider.
        
        Args:
            provider: Provider name
            key: API key value
            persist: Whether to persist to secrets.toml
        """
        self._keys[provider] = key
        
        if persist:
            self._persist_key(provider, key)
    
    def _persist_key(self, provider: str, key: str):
        """Persist key to secrets.toml."""
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing secrets
        existing = {}
        if self.secrets_path.exists():
            try:
                import tomllib
                with open(self.secrets_path, "rb") as f:
                    existing = tomllib.load(f)
            except Exception:
                pass
        
        # Update with new key
        existing[f"{provider}_api_key"] = key
        
        # Write back
        import tomli_w
        with open(self.secrets_path, "wb") as f:
            tomli_w.dump(existing, f)
        
        # Set restrictive permissions
        self.secrets_path.chmod(0o600)
    
    def list_configured(self) -> list[str]:
        """List providers with configured API keys."""
        return list(self._keys.keys())
    
    def prompt_missing(self, provider: str) -> str | None:
        """
        Interactively prompt for missing API key.
        
        Returns:
            The entered key, or None if cancelled
        """
        import getpass
        
        if provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        env_var = self.ENV_MAPPINGS[provider]
        
        print(f"\nAPI key required for {provider.upper()}")
        print(f"You can also set the {env_var} environment variable.")
        print(f"Or add it to ~/.streamlitforge/secrets.toml")
        print()
        
        key = getpass.getpass(f"Enter {provider} API key (or press Enter to skip): ")
        
        if key:
            self.set(provider, key)
            return key
        
        return None


def setup_api_keys() -> APIKeyManager:
    """
    Entry point for API key configuration.
    Called during StreamlitForge initialization.
    """
    from .config import StreamlitForgeConfig
    
    config = StreamlitForgeConfig.load()
    manager = APIKeyManager(config)
    
    # Check which providers are available
    configured = manager.list_configured()
    
    if not configured:
        print("\n" + "=" * 60)
        print("StreamlitForge API Key Setup")
        print("=" * 60)
        print("\nNo API keys configured. You can:")
        print("1. Set environment variables (recommended for CI/CD)")
        print("2. Run 'streamlitforge config --setup-keys' for interactive setup")
        print("3. Create ~/.streamlitforge/secrets.toml manually")
        print("\nNote: Ollama (local) does not require an API key.")
        print("=" * 60 + "\n")
    else:
        print(f"\nConfigured providers: {', '.join(configured)}")
    
    return manager
```

### CLI Commands for Key Management

```bash
# Setup keys interactively
streamlitforge config --setup-keys

# Set specific key
streamlitforge config --set-key openai sk-...

# List configured providers
streamlitforge config --list-keys

# Validate keys
streamlitforge config --validate-keys

# Remove key
streamlitforge config --remove-key anthropic
```

### Secrets File Format

```toml
# ~/.streamlitforge/secrets.toml

# OpenAI
openai_api_key = "sk-..."

# Anthropic
anthropic_api_key = "sk-ant-..."

# Groq (free tier)
groq_api_key = "gsk_..."

# Google
google_api_key = "AI..."

# Cohere
cohere_api_key = "..."
```

### Security Best Practices

1. **Never commit secrets files** - Add to .gitignore
2. **Use environment variables in CI/CD** - Most secure for automation
3. **Restrict file permissions** - secrets.toml should be mode 600
4. **Rotate keys periodically** - Use `--validate-keys` to check
5. **Use minimal scopes** - Only grant necessary permissions
6. **Monitor usage** - Check provider dashboards for anomalies

---

## 15. Latent Capabilities (Present but Underutilized)

The following capabilities exist in the MCP ecosystem but are not yet connected to StreamlitForge. Connecting these would unlock significant functionality with minimal implementation effort.

### 15.1 Multi-Agent Code Generation (Hivemind-v2)

**Current State**: Not utilized
**Potential**: Parallel generation of different app components

```
┌─────────────────────────────────────────────────────────────────┐
│                   Hivemind Integration                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Request: "Build a sales dashboard with charts and tables" │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Task Decomposition                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐            │
│         │                    │                    │            │
│         ▼                    ▼                    ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Agent A     │    │ Agent B     │    │ Agent C     │        │
│  │ Layout/Nav  │    │ Charts      │    │ Data Tables │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                    │                    │            │
│         └────────────────────┼────────────────────┘            │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Assembly & Validation                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation**:
```python
class HivemindCodeGenerator:
    """
    Leverage Hivemind-v2 for parallel multi-component generation.
    """
    
    AGENT_TYPES = {
        "layout_specialist": {
            "capabilities": ["layout", "navigation", "responsive"],
            "focus": "Page structure and navigation"
        },
        "data_specialist": {
            "capabilities": ["data", "tables", "caching"],
            "focus": "Data handling and display"
        },
        "chart_specialist": {
            "capabilities": ["charts", "visualization", "altair"],
            "focus": "Data visualization"
        },
        "form_specialist": {
            "capabilities": ["forms", "validation", "input"],
            "focus": "User input handling"
        },
        "auth_specialist": {
            "capabilities": ["authentication", "authorization", "security"],
            "focus": "Security patterns"
        }
    }
    
    async def generate_parallel(
        self,
        spec: AppSpecification,
        components: list[str]
    ) -> dict[str, str]:
        """
        Generate multiple components in parallel using specialized agents.
        
        Args:
            spec: Full app specification
            components: List of components to generate
        
        Returns:
            Map of component name to generated code
        """
        # 1. Register specialized agents
        for agent_type, config in self.AGENT_TYPES.items():
            await self.mcp.call_tool(
                server="hivemind",
                tool="register_agent",
                arguments={
                    "id": f"streamlitforge_{agent_type}",
                    "name": f"StreamlitForge {agent_type}",
                    "type": agent_type,
                    "capabilities": config["capabilities"],
                    "status": "idle"
                }
            )
        
        # 2. Submit component tasks
        task_ids = {}
        for component in components:
            task_id = await self.mcp.call_tool(
                server="hivemind",
                tool="submit_task",
                arguments={
                    "description": f"Generate {component} component",
                    "priority": 5,
                    "estimated_effort": 3,
                    "required_capabilities": self._get_required_capabilities(component)
                }
            )
            task_ids[component] = task_id
        
        # 3. Auto-assign tasks to agents
        await self.mcp.call_tool(
            server="hivemind",
            tool="assign_tasks",
            arguments={}
        )
        
        # 4. Collect results
        results = {}
        for component, task_id in task_ids.items():
            status = await self._wait_for_task(task_id)
            results[component] = status.get("result", {}).get("code")
        
        return results
```

**Latent Value**: 3-5x faster generation for complex multi-component apps

---

### 15.2 Advanced Reasoning (Omega-v2)

**Current State**: Not utilized
**Potential**: Superior architectural decisions through SEAL/RLM reasoning

**Capabilities**:
- SEAL pattern (Study-Extract-Apply-Learn)
- RLM (Recursive Language Model) for deep analysis
- Consensus game for conflict resolution
- Test-time training for adaptation

**Use Cases**:

| Scenario | Omega Tool | Benefit |
|----------|-----------|---------|
| Architecture decision | `strategize` | Explores blind spots, trade-offs |
| Conflict between approaches | `adjudicate_conflict` | Nash equilibrium solution |
| Learning from mistakes | `reflect` | Self-improvement cycle |
| Pattern adaptation | `learn` | Test-time training on examples |

**Implementation**:
```python
class OmegaReasoningEngine:
    """
    Integrate Omega-v2 for advanced architectural reasoning.
    """
    
    async def architectural_guidance(
        self,
        situation: str,
        dilemma: str,
        perspective: str
    ) -> ArchitecturalDecision:
        """
        Get strategic architectural guidance.
        """
        result = await self.mcp.call_tool(
            server="omega",
            tool="strategize",
            arguments={
                "current_situation": situation,
                "dilemma": dilemma,
                "desired_perspective": perspective,
                "method": "seal"
            }
        )
        
        return ArchitecturalDecision(
            recommendation=result.get("recommendation"),
            reasoning=result.get("reasoning"),
            tradeoffs=result.get("tradeoffs"),
            risks=result.get("risks")
        )
    
    async def resolve_conflict(
        self,
        approach_a: str,
        approach_b: str,
        constraints: list[str]
    ) -> ConflictResolution:
        """
        Resolve architectural conflicts using consensus game.
        """
        result = await self.mcp.call_tool(
            server="omega",
            tool="adjudicate_conflict",
            arguments={
                "conflict_description": f"Approach A: {approach_a}\nApproach B: {approach_b}",
                "opposing_forces": constraints,
                "domain": "streamlit"
            }
        )
        
        return ConflictResolution(
            winner=result.get("consensus"),
            reasoning=result.get("reasoning"),
            agreement_score=result.get("agreement_score")
        )
```

**Latent Value**: Prevents architectural mistakes, resolves team conflicts objectively

---

### 15.3 Semantic Code Intelligence (Context-Singularity-v2)

**Current State**: Not utilized
**Potential**: "Find similar code", "Explain this function", trace origins

**Capabilities**:
- Code indexing with AST analysis
- Semantic search across codebase
- Function/class dependency tracking
- Origin tracing

**Use Cases**:
```python
class SemanticCodeIntelligence:
    """
    Integrate Context-Singularity for semantic code understanding.
    """
    
    async def index_project(self, project_path: str) -> dict:
        """Index a project for semantic search."""
        return await self.mcp.call_tool(
            server="context-singularity",
            tool="ingest_codebase",
            arguments={
                "root_path": project_path,
                "pattern": "**/*.py"
            }
        )
    
    async def find_similar_code(
        self,
        query: str,
        limit: int = 10
    ) -> list[CodeMatch]:
        """Find similar code patterns in indexed projects."""
        result = await self.mcp.call_tool(
            server="context-singularity",
            tool="ask",
            arguments={
                "query": query,
                "limit": limit
            }
        )
        return result.get("results", [])
    
    async def explain_element(
        self,
        element_id: str
    ) -> ElementExplanation:
        """Get detailed explanation of a code element."""
        return await self.mcp.call_tool(
            server="context-singularity",
            tool="explain",
            arguments={"element_id": element_id}
        )
    
    async def trace_origin(self, function_name: str) -> OriginTrace:
        """Trace where a function/class originated."""
        return await self.mcp.call_tool(
            server="context-singularity",
            tool="trace_origin",
            arguments={"name": function_name}
        )
    
    async def find_impact(self, element_id: str) -> ImpactAnalysis:
        """Find what would be affected by changing this element."""
        return await self.mcp.call_tool(
            server="context-singularity",
            tool="find_impact",
            arguments={"element_id": element_id}
        )
```

**Latent Value**: Enables "smart copy" from existing projects, impact analysis

---

### 15.4 Process Orchestration (Floyd-Terminal)

**Current State**: Not utilized
**Potential**: Manage all running Streamlit apps from one dashboard

**Capabilities**:
- Start/stop/rerun processes
- Interact with running processes
- Monitor resource usage
- Session persistence

**Implementation**:
```python
class StreamlitProcessManager:
    """
    Manage running Streamlit applications.
    """
    
    async def start_app(
        self,
        project_path: str,
        port: int,
        detached: bool = True
    ) -> ProcessSession:
        """Start a Streamlit app."""
        result = await self.mcp.call_tool(
            server="floyd-terminal",
            tool="start_process",
            arguments={
                "command": "streamlit",
                "args": ["run", "src/app.py", "--server.port", str(port)],
                "cwd": project_path,
                "detached": detached,
                "sessionName": f"streamlit_{Path(project_path).name}"
            }
        )
        
        return ProcessSession(
            session_id=result.get("sessionId"),
            pid=result.get("pid"),
            port=port
        )
    
    async def list_apps(self) -> list[RunningApp]:
        """List all running Streamlit apps."""
        result = await self.mcp.call_tool(
            server="floyd-terminal",
            tool="list_processes",
            arguments={"filter": "streamlit"}
        )
        return [RunningApp(**app) for app in result.get("processes", [])]
    
    async def stop_app(self, session_id: str) -> bool:
        """Stop a running app."""
        await self.mcp.call_tool(
            server="floyd-terminal",
            tool="force_terminate",
            arguments={"sessionId": session_id}
        )
        return True
    
    async def restart_app(self, session_id: str) -> ProcessSession:
        """Restart an app (useful after code changes)."""
        # Get session info
        sessions = await self.mcp.call_tool(
            server="floyd-terminal",
            tool="list_sessions",
            arguments={}
        )
        session = next(s for s in sessions if s["sessionId"] == session_id)
        
        # Stop and restart
        await self.stop_app(session_id)
        return await self.start_app(session["cwd"], session["port"])
```

**Latent Value**: Unified dashboard for all Streamlit apps, one-click restart

---

### 15.5 UI Visual Testing (ZAI Vision)

**Current State**: Not utilized
**Potential**: Compare generated UI against design specs

**Capabilities**:
- Screenshot analysis
- UI diff comparison
- Error diagnosis from screenshots
- Design-to-code extraction

**Implementation**:
```python
class UIVisualTester:
    """
    Visual testing for generated Streamlit apps.
    """
    
    async def compare_ui(
        self,
        expected_image: str,
        actual_screenshot: str
    ) -> UIDiffResult:
        """Compare expected design with actual implementation."""
        result = await self.mcp.call_tool(
            server="zai-mcp-server",
            tool="ui_diff_check",
            arguments={
                "expected_image_source": expected_image,
                "actual_image_source": actual_screenshot,
                "prompt": "Compare these UIs and identify differences in layout, colors, spacing, and components"
            }
        )
        
        return UIDiffResult(
            match_score=result.get("match_score"),
            differences=result.get("differences"),
            suggestions=result.get("suggestions")
        )
    
    async def diagnose_error(
        self,
        screenshot_path: str,
        context: str
    ) -> ErrorDiagnosis:
        """Diagnose errors from screenshots."""
        result = await self.mcp.call_tool(
            server="zai-mcp-server",
            tool="diagnose_error_screenshot",
            arguments={
                "image_source": screenshot_path,
                "prompt": "What error is shown and how can I fix it?",
                "context": context
            }
        )
        
        return ErrorDiagnosis(
            error_type=result.get("error_type"),
            message=result.get("message"),
            solution=result.get("solution")
        )
    
    async def extract_design_specs(
        self,
        design_image: str
    ) -> DesignSpecs:
        """Extract design specifications from an image."""
        result = await self.mcp.call_tool(
            server="zai-mcp-server",
            tool="ui_to_artifact",
            arguments={
                "image_source": design_image,
                "output_type": "spec",
                "prompt": "Extract complete design specifications including colors, fonts, spacing, and component hierarchy"
            }
        )
        
        return DesignSpecs.from_dict(result)
```

**Latent Value**: Automated UI validation, design-to-code workflow

---

### 15.6 Episodic Learning (Novel-Concepts)

**Current State**: Not utilized
**Potential**: Learn from successes and failures automatically

**Implementation**:
```python
class EpisodicLearning:
    """
    Learn from generation episodes for continuous improvement.
    """
    
    async def record_episode(
        self,
        trigger: str,
        reasoning: str,
        solution: str,
        outcome: str,
        metadata: dict = None
    ) -> str:
        """Record a generation episode."""
        result = await self.mcp.call_tool(
            server="novel-concepts",
            tool="episodic_memory_bank",
            arguments={
                "action": "store",
                "episode": {
                    "trigger": trigger,
                    "reasoning": reasoning,
                    "solution": solution,
                    "outcome": outcome,
                    "metadata": metadata or {}
                }
            }
        )
        return result.get("episode_id")
    
    async def retrieve_similar_episodes(
        self,
        query: str,
        max_results: int = 3
    ) -> list[Episode]:
        """Find similar past episodes."""
        result = await self.mcp.call_tool(
            server="novel-concepts",
            tool="episodic_memory_bank",
            arguments={
                "action": "retrieve",
                "query": query,
                "max_results": max_results
            }
        )
        return [Episode(**e) for e in result.get("episodes", [])]
    
    async def adapt_solution(
        self,
        current_context: str,
        query: str
    ) -> AdaptedSolution:
        """Adapt a past solution to current context."""
        result = await self.mcp.call_tool(
            server="novel-concepts",
            tool="episodic_memory_bank",
            arguments={
                "action": "adapt",
                "query": query,
                "current_context": current_context,
                "max_results": 3
            }
        )
        return AdaptedSolution.from_dict(result)
```

**Latent Value**: Gets smarter over time, avoids repeating mistakes

---

### 15.7 Consensus-Based Decision Making (Novel-Concepts)

**Current State**: Not utilized
**Potential**: Multi-perspective analysis for important decisions

**Implementation**:
```python
class ConsensusDecisionMaker:
    """
    Multi-perspective consensus for architectural decisions.
    """
    
    async def evaluate_decision(
        self,
        question: str,
        perspectives: list[str] = None
    ) -> ConsensusResult:
        """
        Evaluate a decision from multiple perspectives.
        
        Perspectives: optimistic, pessimistic, pragmatic, security,
                      performance, maintainability, user_experience, cost
        """
        result = await self.mcp.call_tool(
            server="novel-concepts",
            tool="consensus_protocol",
            arguments={
                "question": question,
                "domain": "streamlit",
                "perspectives": perspectives or [
                    "optimistic", "pessimistic", "pragmatic",
                    "security", "performance"
                ],
                "consensus_threshold": 0.7
            }
        )
        
        return ConsensusResult(
            recommendation=result.get("recommendation"),
            confidence=result.get("confidence"),
            agreed_points=result.get("agreed_points"),
            disagreed_points=result.get("disagreed_points"),
            caveats=result.get("caveats")
        )
```

**Latent Value**: Reduces risk of bad architectural decisions

---

### 15.8 Auto-Validation Pipeline (Floyd-Runner)

**Current State**: Not utilized
**Potential**: Auto-validate all generated code

**Implementation**:
```python
class AutoValidationPipeline:
    """
    Automatically validate generated code.
    """
    
    async def validate(
        self,
        project_path: str,
        checks: list[str] = None
    ) -> ValidationResult:
        """
        Run validation checks on generated code.
        
        Checks: lint, typecheck, test, format, security
        """
        results = {}
        
        if "lint" in (checks or ["lint"]):
            results["lint"] = await self.mcp.call_tool(
                server="floyd-runner",
                tool="lint",
                arguments={"path": project_path}
            )
        
        if "typecheck" in (checks or []):
            results["typecheck"] = await self.mcp.call_tool(
                server="floyd-runner",
                tool="typecheck",
                arguments={"path": project_path}
            )
        
        if "test" in (checks or []):
            results["test"] = await self.mcp.call_tool(
                server="floyd-runner",
                tool="test",
                arguments={
                    "path": project_path,
                    "command": "pytest"
                }
            )
        
        if "format" in (checks or []):
            results["format"] = await self.mcp.call_tool(
                server="floyd-runner",
                tool="format",
                arguments={
                    "path": project_path,
                    "fix": True
                }
            )
        
        return ValidationResult(
            passed=all(r.get("success", False) for r in results.values()),
            results=results
        )
```

**Latent Value**: Ensures generated code is production-ready

---

### 15.9 Dependency Hologram (Gemini-Tools)

**Current State**: Not utilized
**Potential**: Visualize and analyze complex dependencies

**Implementation**:
```python
class DependencyVisualizer:
    """
    Visualize project dependencies as a hologram.
    """
    
    async def generate_hologram(
        self,
        project_path: str,
        output_format: str = "svg"
    ) -> DependencyHologram:
        """Generate a visual dependency hologram."""
        result = await self.mcp.call_tool(
            server="gemini-tools",
            tool="dependency_hologram",
            arguments={
                "action": "generate",
                "project_path": project_path,
                "output_format": output_format
            }
        )
        
        return DependencyHologram(
            image_data=result.get("image"),
            modules=result.get("modules"),
            connections=result.get("connections"),
            circular_deps=result.get("circular_dependencies")
        )
```

**Latent Value**: Visual debugging of complex apps

---

### 15.10 Web Knowledge Grounding (Web-Search + Web-Reader)

**Current State**: Partially utilized
**Potential**: Real-time grounding with latest Streamlit docs

**Implementation**:
```python
class WebKnowledgeGrounding:
    """
    Real-time web grounding for Streamlit knowledge.
    """
    
    async def search_latest(
        self,
        query: str,
        recency: str = "oneWeek"
    ) -> list[SearchResult]:
        """Search for latest Streamlit information."""
        result = await self.mcp.call_tool(
            server="web-search-prime",
            tool="webSearchPrime",
            arguments={
                "search_query": f"streamlit {query}",
                "search_recency_filter": recency,
                "content_size": "medium"
            }
        )
        return result.get("results", [])
    
    async def read_documentation(
        self,
        url: str
    ) -> str:
        """Read and parse documentation page."""
        result = await self.mcp.call_tool(
            server="web-reader",
            tool="webReader",
            arguments={
                "url": url,
                "return_format": "markdown",
                "retain_images": False
            }
        )
        return result.get("content", "")
    
    async def get_latest_examples(
        self,
        component: str
    ) -> list[CodeExample]:
        """Find latest code examples for a component."""
        # Search GitHub for recent examples
        result = await self.mcp.call_tool(
            server="zread",
            tool="search_doc",
            arguments={
                "repo_name": "streamlit/streamlit",
                "query": component,
                "language": "en"
            }
        )
        return result.get("examples", [])
```

**Latent Value**: Always up-to-date with latest Streamlit features

---

## 16. Proactive Enhancements (New Capabilities)

The following enhancements would significantly improve StreamlitForge beyond what's currently planned.

### 16.1 Live Preview Integration

**Concept**: Real-time preview of generated code as user types

```python
class LivePreviewManager:
    """
    Live preview of generated Streamlit code.
    Uses hot-reload for instant feedback.
    """
    
    def __init__(self):
        self.preview_sessions: dict[str, ProcessSession] = {}
    
    async def start_preview(
        self,
        code: str,
        port: int
    ) -> str:
        """Start a live preview session."""
        # Write code to temp file
        temp_path = self._write_temp(code)
        
        # Start Streamlit with hot-reload
        session = await self.mcp.call_tool(
            server="floyd-terminal",
            tool="start_process",
            arguments={
                "command": "streamlit",
                "args": ["run", str(temp_path), "--server.port", str(port)],
                "detached": True
            }
        )
        
        self.preview_sessions[port] = session
        return f"http://localhost:{port}"
    
    async def update_preview(
        self,
        port: int,
        new_code: str
    ):
        """Update preview with new code (triggers hot-reload)."""
        session = self.preview_sessions.get(port)
        if session:
            temp_path = self._get_temp_path(port)
            Path(temp_path).write_text(new_code)
            # Streamlit auto-reloads on file change
```

---

### 16.2 Component Marketplace

**Concept**: Browse and install community Streamlit components

```python
class ComponentMarketplace:
    """
    Marketplace for Streamlit components.
    """
    
    async def search_components(
        self,
        query: str,
        category: str = None
    ) -> list[ComponentListing]:
        """Search for components."""
        results = await self.web_knowledge.search_latest(
            f"streamlit component {query}"
        )
        
        # Filter and rank by:
        # - GitHub stars
        # - PyPI downloads
        # - Last update date
        # - Documentation quality
        
        return self._rank_results(results)
    
    async def install_component(
        self,
        component_name: str,
        project_path: str
    ) -> InstallationResult:
        """Install a component into project."""
        # 1. pip install
        # 2. Add to requirements.txt
        # 3. Generate usage example
        # 4. Update imports
        pass
```

---

### 16.3 AI-Powered Code Review

**Concept**: Automated code review for Streamlit best practices

```python
class StreamlitCodeReviewer:
    """
    AI-powered code review for Streamlit apps.
    """
    
    async def review(
        self,
        code: str,
        review_type: str = "comprehensive"
    ) -> CodeReview:
        """Perform comprehensive code review."""
        
        # Use Senior Developer persona with code context
        review_prompt = f"""
        Review this Streamlit code for:
        1. Best practices violations
        2. Performance issues
        3. Security concerns
        4. Deprecated API usage
        5. State management issues
        6. Accessibility problems
        
        Code:
        ```python
        {code}
        ```
        """
        
        # Get consensus from multiple perspectives
        consensus = await self.consensus.evaluate_decision(
            question=f"Is this code production-ready?",
            perspectives=["security", "performance", "maintainability"]
        )
        
        # Check against known patterns
        patterns = await self.patterns.retrieve_similar_episodes(code)
        
        return CodeReview(
            score=consensus.confidence * 10,
            issues=self._extract_issues(consensus),
            suggestions=consensus.caveats,
            similar_patterns=patterns
        )
```

---

### 16.4 Intelligent Error Resolution

**Concept**: Auto-diagnose and fix common Streamlit errors

```python
class ErrorResolver:
    """
    Intelligent error resolution for Streamlit apps.
    """
    
    KNOWN_ERRORS = {
        "SessionState has no attribute": {
            "cause": "Accessing undefined session state key",
            "fix": "Initialize with st.session_state.get('key', default)"
        },
        "DuplicateWidgetID": {
            "cause": "Multiple widgets with same key",
            "fix": "Ensure unique keys for all widgets"
        },
        "ScriptRunContext missing": {
            "cause": "Using Streamlit commands outside main thread",
            "fix": "Ensure all Streamlit calls are in main execution"
        }
    }
    
    async def diagnose(
        self,
        error_message: str,
        code: str = None,
        screenshot: str = None
    ) -> ErrorDiagnosis:
        """Diagnose error and suggest fix."""
        
        # 1. Check known errors
        for pattern, info in self.KNOWN_ERRORS.items():
            if pattern in error_message:
                return ErrorDiagnosis(
                    error_type=pattern,
                    cause=info["cause"],
                    fix=info["fix"],
                    confidence=0.9
                )
        
        # 2. Use vision if screenshot provided
        if screenshot:
            return await self.vision_tester.diagnose_error(
                screenshot, error_message
            )
        
        # 3. Use LLM for unknown errors
        return await self._llm_diagnose(error_message, code)
    
    async def auto_fix(
        self,
        error: ErrorDiagnosis,
        code: str
    ) -> str:
        """Automatically apply fix to code."""
        # Use safe-ops for safe modification
        operations = self._generate_fix_operations(error, code)
        
        result = await self.safe_ops.refactor(
            operations=operations,
            verify_command=f"python -m py_compile app.py"
        )
        
        return result.get("code", code)
```

---

### 16.5 Usage Analytics Dashboard

**Concept**: Track and visualize StreamlitForge usage patterns

```python
class UsageAnalytics:
    """
    Analytics for StreamlitForge usage.
    """
    
    async def track_generation(
        self,
        prompt: str,
        generated_code: str,
        accepted: bool,
        modifications: str = None
    ):
        """Track a code generation event."""
        await self.mcp.call_tool(
            server="floyd-supercache",
            tool="cache_store",
            arguments={
                "key": f"analytics_{datetime.now().isoformat()}",
                "value": {
                    "prompt": prompt,
                    "accepted": accepted,
                    "had_modifications": modifications is not None,
                    "code_length": len(generated_code),
                    "timestamp": datetime.now().isoformat()
                },
                "tier": "project",
                "tags": ["analytics", "generation"]
            }
        )
    
    async def get_stats(self) -> UsageStats:
        """Get usage statistics."""
        results = await self.mcp.call_tool(
            server="floyd-supercache",
            tool="cache_search",
            arguments={
                "query": "analytics generation",
                "tier": "project"
            }
        )
        
        return UsageStats(
            total_generations=len(results),
            acceptance_rate=self._calc_acceptance_rate(results),
            common_patterns=self._extract_patterns(results),
            improvement_trend=self._calc_trend(results)
        )
```

---

### 16.6 Collaboration Features

**Concept**: Multi-user collaboration on Streamlit projects

```python
class CollaborationManager:
    """
    Multi-user collaboration for StreamlitForge.
    """
    
    async def create_project_session(
        self,
        project_id: str,
        owner: str
    ) -> CollaborationSession:
        """Create a collaborative session."""
        result = await self.mcp.call_tool(
            server="hivemind",
            tool="collaborate",
            arguments={
                "participants": [owner],
                "task_id": project_id
            }
        )
        
        return CollaborationSession(
            session_id=result.get("collaboration_id"),
            project_id=project_id,
            owner=owner
        )
    
    async def join_session(
        self,
        session_id: str,
        user_id: str
    ):
        """Join a collaborative session."""
        pass
    
    async def propose_change(
        self,
        session_id: str,
        user_id: str,
        change: dict
    ) -> ChangeProposal:
        """Propose a change for consensus."""
        # Use consensus protocol for team decisions
        consensus = await self.consensus.evaluate_decision(
            question=f"Should we accept this change: {change['description']}?",
            perspectives=["maintainability", "security", "performance"]
        )
        
        return ChangeProposal(
            change=change,
            approved=consensus.confidence > 0.7,
            concerns=consensus.disagreed_points
        )
```

---

## 17. Integration Matrix

Summary of all MCP integrations and their status:

| MCP Server | Tools | Status | Priority | Use Case |
|------------|-------|--------|----------|----------|
| floyd-supercache | 12 | Integrated | Critical | Pattern/reasoning storage |
| floyd-devtools | 6 | Integrated | High | Dependency analysis |
| floyd-safe-ops | 3 | Integrated | Critical | Safe refactoring |
| floyd-terminal | 9 | Latent | High | Process management |
| hivemind-v2 | 11 | Latent | High | Multi-agent generation |
| omega-v2 | 6 | Latent | Medium | Advanced reasoning |
| context-singularity | 9 | Latent | High | Semantic code search |
| novel-concepts | 10 | Latent | Medium | Consensus/episodic learning |
| floyd-runner | 6 | Latent | High | Auto-validation |
| floyd-git | 7 | Latent | Medium | Version control |
| gemini-tools | 3 | Latent | Low | Dependency hologram |
| zai-mcp-server | 8 | Latent | Medium | UI visual testing |
| web-search-prime | 1 | Latent | High | Knowledge grounding |
| web-reader | 1 | Latent | High | Documentation parsing |

---

## Appendix: Pattern Library Examples

### Data Table Pattern
```python
# Trigger: "table", "data", "grid", "datatable"
# Variables: enable_search, enable_export, enable_pagination, enable_sort

PATTERN = '''
def render_{component_name}_table(
    data: pd.DataFrame,
    title: str = "Data Table",
    {variables}
) -> pd.DataFrame:
    """Render {component_name} data table with {features}."""
    
    st.subheader(title)
    
    {search_logic}
    {export_logic}
    {pagination_logic}
    
    st.dataframe(data, use_container_width=True)
    return data
'''
```

### Chart Pattern
```python
# Trigger: "chart", "graph", "plot", "visualization"
# Variables: chart_type, enable_zoom, enable_download

PATTERN = '''
def render_{component_name}_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    chart_type: str = "{default_chart_type}",
    title: str = "{component_name}"
) -> None:
    """Render {component_name} chart."""
    
    import altair as alt
    
    st.subheader(title)
    
    chart = alt.Chart(data).mark_{mark_type}().encode(
        x=alt.X(x_col),
        y=alt.Y(y_col)
    )
    
    st.altair_chart(chart, use_container_width=True)
'''
```

---

## Appendix: Streamly Integration Reference

### Key Streamly Features Incorporated

| Feature | Streamly Implementation | StreamlitForge Enhancement |
|---------|------------------------|---------------------------|
| Chat Interface | st.chat_input/message | Multi-mode chat (Chat/Build/Expert) |
| Session Memory | st.session_state | Persistent + exportable |
| Updates Feed | JSON file | Auto-updating web grounding |
| Code Snippets | LLM generated | LLM + pattern library fallback |
| Custom Styling | CSS in markdown | Theme system + custom CSS |
| Mode Selection | Radio button | Tab-based with mode-specific UI |

### Streamly Patterns Adapted

```python
# From Streamly: Conversation initialization
def initialize_conversation():
    return [
        {"role": "system", "content": "You are StreamlitForge..."},
        {"role": "system", "content": "Trained on Streamlit 1.x..."},
        {"role": "assistant", "content": "Welcome message..."}
    ]

# Enhanced with: Persona injection
def initialize_with_persona(persona: str = "builder"):
    base = initialize_conversation()
    persona_prompts = {
        "builder": "Focus on code generation...",
        "expert": "15+ years experience...",
        "teacher": "Explain step by step..."
    }
    base.insert(1, {"role": "system", "content": persona_prompts[persona]})
    return base
```

---

*Document Version: 4.0*
*Last Updated: 2026-03-03*
*Author: StreamlitForge Planning Team*
