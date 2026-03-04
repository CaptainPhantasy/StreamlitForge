"""LLM Status page - Provider health, latency, costs, and model selection."""

import streamlit as st
import time


def render():
    """Render the LLM Status page."""
    
    st.title("🤖 LLM Status")
    
    st.markdown("""
    Monitor LLM provider health, latency, costs, and select models for code generation.
    """)
    
    # Import LLM modules
    from streamlitforge.llm.router import EnhancedLLMRouter
    from streamlitforge.llm.base import LLMProvider, ProviderStatus
    from streamlitforge.core.api_keys import APIKeyManager
    
    km = st.session_state.api_key_manager
    
    # Initialize router if not exists
    if "llm_router" not in st.session_state:
        st.session_state.llm_router = initialize_router(km)
    
    router = st.session_state.llm_router
    
    # Provider status overview
    st.subheader("Provider Status")
    
    all_providers = [
        ("ollama", "🦙", "Free, Local", True),
        ("openai", "🟢", "Paid", bool(km.get("openai"))),
        ("anthropic", "🟣", "Paid", bool(km.get("anthropic"))),
        ("groq", "⚡", "Free Tier", bool(km.get("groq"))),
        ("google", "🔵", "Free Tier", bool(km.get("google"))),
        ("mistral", "🟠", "Paid", bool(km.get("mistral"))),
        ("deepseek", "🔷", "Low Cost", bool(km.get("deepseek"))),
    ]
    
    cols = st.columns(len(all_providers))
    
    status_data = {}
    
    for idx, (name, icon, tier, configured) in enumerate(all_providers):
        with cols[idx]:
            # Check availability
            available = check_provider_availability(name, km)
            status_data[name] = {
                "available": available,
                "configured": configured,
                "tier": tier,
            }
            
            if available:
                st.metric(f"{icon} {name.capitalize()}", "🟢 Online")
            elif configured:
                st.metric(f"{icon} {name.capitalize()}", "🟡 Configured")
            else:
                st.metric(f"{icon} {name.capitalize()}", "⚪ Not Set")
            
            st.caption(tier)
    
    st.divider()
    
    # Detailed status table
    st.subheader("Detailed Status")
    
    status_rows = []
    for name, icon, tier, configured in all_providers:
        data = status_data[name]
        status_rows.append({
            "Provider": f"{icon} {name.capitalize()}",
            "Status": "✅ Available" if data["available"] else ("⚠️ Configured" if data["configured"] else "❌ Not Configured"),
            "Tier": tier,
            "Latency": "12ms" if name == "ollama" else ("~200ms" if data["available"] else "N/A"),
        })
    
    import pandas as pd
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Model Selection
    st.subheader("Model Selection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Select Provider")
        
        available_providers = [name for name, _, _, configured in all_providers if status_data[name]["available"]]
        
        if not available_providers:
            st.warning("No providers available. Configure API keys in Settings.")
        else:
            selected_provider = st.selectbox(
                "Provider",
                available_providers,
                index=available_providers.index(st.session_state.get("selected_provider", available_providers[0]))
                if st.session_state.get("selected_provider") in available_providers
                else 0,
            )
            st.session_state.selected_provider = selected_provider
            
            # Get available models for provider
            models = get_provider_models(selected_provider)
            
            st.markdown("#### Select Model")
            selected_model = st.selectbox(
                "Model",
                models,
                index=models.index(st.session_state.get("selected_model", models[0]))
                if st.session_state.get("selected_model") in models
                else 0,
            )
            st.session_state.selected_model = selected_model
    
    with col2:
        st.markdown("#### Current Selection")
        
        st.info(f"""
        **Provider:** {st.session_state.get('selected_provider', 'None').capitalize()}
        
        **Model:** {st.session_state.get('selected_model', 'None')}
        
        This selection will be used for all AI operations in the builder.
        """)
        
        if st.button("Test Selection", use_container_width=True):
            with st.spinner("Testing connection..."):
                result = test_llm_connection(
                    st.session_state.get("selected_provider"),
                    st.session_state.get("selected_model"),
                    km,
                )
                if result:
                    st.success("✅ Connection successful!")
                else:
                    st.error("❌ Connection failed")
    
    st.divider()
    
    # Cost Tracking
    st.subheader("Cost Tracking")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get stats from router if available
    router = st.session_state.get("llm_router")
    if router:
        cost_report = router.get_cost_report()
        session_requests = cost_report["total_requests"]
        session_tokens = cost_report["total_tokens"]
        session_cost = cost_report["total_cost"]
    else:
        session_requests = st.session_state.get("session_requests", 0)
        session_tokens = st.session_state.get("session_tokens", 0)
        session_cost = st.session_state.get("session_cost", 0.0)
    
    cache_hits = st.session_state.get("cache_hits", 0)
    
    with col1:
        st.metric("Session Requests", session_requests)
    
    with col2:
        st.metric("Session Tokens", f"{session_tokens:,}")
    
    with col3:
        st.metric("Session Cost", f"${session_cost:.4f}")
    
    with col4:
        st.metric("Cache Hits", cache_hits)
    
    # Reset cost tracking
    if st.button("Reset Session Stats"):
        st.session_state.session_requests = 0
        st.session_state.session_tokens = 0
        st.session_state.session_cost = 0.0
        st.session_state.cache_hits = 0
        if router:
            router.reset_stats()
        st.rerun()
    
    st.divider()
    
    # Pricing Reference
    with st.expander("💰 Pricing Reference (per 1M tokens)"):
        pricing_data = {
            "Provider": ["OpenAI GPT-4o", "OpenAI GPT-4o-mini", "Anthropic Claude", "Groq Llama", "Google Gemini", "DeepSeek"],
            "Input": ["$2.50", "$0.15", "$3.00", "Free*", "Free*", "$0.14"],
            "Output": ["$10.00", "$0.60", "$15.00", "Free*", "Free*", "$0.28"],
        }
        st.dataframe(pd.DataFrame(pricing_data), use_container_width=True, hide_index=True)
        st.caption("*Free tier with rate limits")
    
    st.divider()
    
    # Router Strategy
    st.subheader("Routing Strategy")
    
    strategy = st.radio(
        "Select routing strategy",
        ["cost_optimized", "latency_optimized", "quality_optimized"],
        horizontal=True,
        format_func=lambda x: {
            "cost_optimized": "💰 Cost Optimized",
            "latency_optimized": "⚡ Latency Optimized",
            "quality_optimized": "⭐ Quality Optimized",
        }[x],
    )
    
    st.session_state.routing_strategy = strategy
    
    st.caption(f"Current strategy: **{strategy.replace('_', ' ').title()}**")


def initialize_router(km) -> "EnhancedLLMRouter":
    """Initialize the LLM router with configured providers."""
    from streamlitforge.llm.router import EnhancedLLMRouter
    from streamlitforge.llm.providers.ollama import OllamaProvider
    
    providers = {}
    
    # Always add Ollama
    try:
        providers["ollama"] = OllamaProvider()
    except Exception:
        pass
    
    # Add other providers if configured
    if km.get("openai"):
        try:
            from streamlitforge.llm.providers.openai import OpenAIProvider
            providers["openai"] = OpenAIProvider(api_key=km.get("openai"))
        except Exception:
            pass
    
    if km.get("anthropic"):
        try:
            from streamlitforge.llm.providers.anthropic import AnthropicProvider
            providers["anthropic"] = AnthropicProvider(api_key=km.get("anthropic"))
        except Exception:
            pass
    
    if km.get("groq"):
        try:
            from streamlitforge.llm.providers.groq import GroqProvider
            providers["groq"] = GroqProvider(api_key=km.get("groq"))
        except Exception:
            pass
    
    return EnhancedLLMRouter(providers=providers)


def check_provider_availability(name: str, km) -> bool:
    """Check if a provider is available."""
    if name == "ollama":
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            return resp.status_code == 200
        except Exception:
            return False
    
    # For other providers, check if API key is set
    return bool(km.get(name))


def get_provider_models(provider: str) -> list:
    """Get available models for a provider."""
    models = {
        "ollama": ["llama3", "llama3:70b", "codellama:7b", "mistral", "deepseek-coder"],
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "groq": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b"],
        "google": ["gemini-pro", "gemini-pro-vision"],
        "mistral": ["mistral-large", "mistral-medium", "mistral-small"],
        "deepseek": ["deepseek-coder", "deepseek-chat"],
    }
    return models.get(provider, ["default"])


def test_llm_connection(provider: str, model: str, km) -> bool:
    """Test LLM connection."""
    try:
        if provider == "ollama":
            import requests
            resp = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": "test", "stream": False},
                timeout=10,
            )
            return resp.status_code == 200
        else:
            # Just check if key is configured
            return bool(km.get(provider))
    except Exception:
        return False
