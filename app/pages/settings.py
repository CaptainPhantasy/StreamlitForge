"""Settings page for StreamlitForge."""

import streamlit as st
from pathlib import Path
import json


SETTINGS_FILE = Path.home() / ".streamlitforge" / "settings.json"


def load_settings() -> dict:
    """Load settings from file."""
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_settings(settings: dict):
    """Save settings to file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


def render():
    """Render the Settings page."""
    
    st.title("⚙️ Settings")
    
    # Load current settings
    current_settings = load_settings()
    
    tab_api, tab_general, tab_about = st.tabs(["API Keys", "General", "About"])
    
    with tab_api:
        st.subheader("🔑 LLM Provider API Keys")
        
        st.markdown("""
        Configure your LLM providers. At least one provider is required for AI features.
        API keys are stored locally and never sent to external servers.
        """)
        
        st.divider()
        
        km = st.session_state.api_key_manager
        
        # OpenAI
        with st.container(border=True):
            st.markdown("### 🟢 OpenAI")
            current = km.get("openai")
            if current:
                st.caption(f"Current: {current[:8]}...{current[-4:]}")
            
            key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...", key="openai_key")
            if st.button("Save", key="save_openai"):
                if key:
                    km.set("openai", key)
                    st.success("Saved!")
                    st.rerun()
        
        st.divider()
        
        # Anthropic
        with st.container(border=True):
            st.markdown("### 🟣 Anthropic")
            current = km.get("anthropic")
            if current:
                st.caption(f"Current: {current[:8]}...{current[-4:]}")
            
            key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...", key="anthropic_key")
            if st.button("Save", key="save_anthropic"):
                if key:
                    km.set("anthropic", key)
                    st.success("Saved!")
                    st.rerun()
        
        st.divider()
        
        # Ollama
        with st.container(border=True):
            st.markdown("### 🦙 Ollama (Free, Local)")
            st.caption("No API key required - runs locally")
            
            if st.button("Test Ollama Connection", key="test_ollama"):
                if test_ollama():
                    st.success("Ollama is running!")
                else:
                    st.error("Ollama not found. Install: `brew install ollama && ollama serve`")
        
        st.divider()
        
        # Groq
        with st.container(border=True):
            st.markdown("### ⚡ Groq (Free Tier)")
            current = km.get("groq")
            if current:
                st.caption(f"Current: {current[:8]}...{current[-4:]}")
            
            key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", key="groq_key")
            if st.button("Save", key="save_groq"):
                if key:
                    km.set("groq", key)
                    st.success("Saved!")
                    st.rerun()
        
        st.divider()
        
        # Google
        with st.container(border=True):
            st.markdown("### 🔵 Google (Gemini)")
            current = km.get("google")
            if current:
                st.caption(f"Current: {current[:8]}...{current[-4:]}")
            
            key = st.text_input("Google API Key", type="password", placeholder="AIza...", key="google_key")
            if st.button("Save", key="save_google"):
                if key:
                    km.set("google", key)
                    st.success("Saved!")
                    st.rerun()
        
        st.divider()
        
        # OpenRouter
        with st.container(border=True):
            st.markdown("### 🔀 OpenRouter")
            st.caption("Unified API for 100+ models (OpenAI, Anthropic, Google, Meta, Mistral, etc.)")
            current = km.get("openrouter")
            if current:
                st.caption(f"Current: {current[:8]}...{current[-4:]}")
            
            key = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-...", key="openrouter_key")
            if st.button("Save", key="save_openrouter"):
                if key:
                    km.set("openrouter", key)
                    st.success("Saved!")
                    st.rerun()
        
        st.divider()
        
        # OpenCode
        with st.container(border=True):
            st.markdown("### 🧠 OpenCode (Zen & Go)")
            st.caption("Access to Claude, GPT-5, Gemini 3, DeepSeek, and FREE models")
            current = km.get("opencode")
            if current:
                st.caption(f"Current: {current[:8]}...{current[-4:]}")
            
            key = st.text_input("OpenCode API Key", type="password", placeholder="oc_...", key="opencode_key")
            if st.button("Save", key="save_opencode"):
                if key:
                    km.set("opencode", key)
                    st.success("Saved!")
                    st.rerun()
            
            st.caption("Free models available: minimax-m2.5-free, big-pickle, gpt-5-nano")
    
    with tab_general:
        st.subheader("General Settings")
        
        # Project settings
        default_project_location = st.text_input(
            "Default Project Location",
            value=current_settings.get("default_project_location", str(Path.home() / "streamlit_projects")),
        )
        
        col1, col2 = st.columns(2)
        with col1:
            base_port = st.number_input(
                "Base Port",
                value=current_settings.get("base_port", 8501),
                min_value=1024,
                max_value=65535,
            )
        with col2:
            max_port = st.number_input(
                "Max Port",
                value=current_settings.get("max_port", 8999),
                min_value=1024,
                max_value=65535,
            )
        
        # LLM settings
        st.divider()
        st.subheader("LLM Settings")
        
        default_provider = st.selectbox(
            "Default Provider",
            ["ollama", "openai", "anthropic", "groq", "google", "openrouter", "opencode"],
            index=["ollama", "openai", "anthropic", "groq", "google", "openrouter", "opencode"].index(
                current_settings.get("default_provider", "ollama")
            ) if current_settings.get("default_provider") in ["ollama", "openai", "anthropic", "groq", "google", "openrouter", "opencode"] else 0,
        )
        
        default_model = st.text_input(
            "Default Model",
            value=current_settings.get("default_model", "llama3"),
        )
        
        routing_strategy = st.radio(
            "Routing Strategy",
            ["cost_optimized", "latency_optimized", "quality_optimized"],
            index=["cost_optimized", "latency_optimized", "quality_optimized"].index(
                current_settings.get("routing_strategy", "cost_optimized")
            ),
            horizontal=True,
        )
        
        # UI settings
        st.divider()
        st.subheader("UI Settings")
        
        enable_streaming = st.checkbox(
            "Enable Streaming Responses",
            value=current_settings.get("enable_streaming", True),
        )
        
        enable_dark_mode = st.checkbox(
            "Enable Dark Mode (if supported)",
            value=current_settings.get("enable_dark_mode", False),
        )
        
        show_line_numbers = st.checkbox(
            "Show Line Numbers in Code",
            value=current_settings.get("show_line_numbers", True),
        )
        
        # Save button
        st.divider()
        
        if st.button("💾 Save All Settings", type="primary", use_container_width=True):
            new_settings = {
                "default_project_location": default_project_location,
                "base_port": base_port,
                "max_port": max_port,
                "default_provider": default_provider,
                "default_model": default_model,
                "routing_strategy": routing_strategy,
                "enable_streaming": enable_streaming,
                "enable_dark_mode": enable_dark_mode,
                "show_line_numbers": show_line_numbers,
            }
            save_settings(new_settings)
            
            # Update session state
            st.session_state.selected_provider = default_provider
            st.session_state.selected_model = default_model
            st.session_state.routing_strategy = routing_strategy
            st.session_state.use_streaming = enable_streaming
            
            st.success("Settings saved successfully!")
            st.balloons()
        
        # Reset button
        if st.button("🔄 Reset to Defaults", use_container_width=True):
            default_settings = {
                "default_project_location": str(Path.home() / "streamlit_projects"),
                "base_port": 8501,
                "max_port": 8999,
                "default_provider": "ollama",
                "default_model": "llama3",
                "routing_strategy": "cost_optimized",
                "enable_streaming": True,
                "enable_dark_mode": False,
                "show_line_numbers": True,
            }
            save_settings(default_settings)
            st.success("Settings reset to defaults!")
            st.rerun()
        
        # Show settings file location
        st.divider()
        st.caption(f"Settings file: `{SETTINGS_FILE}`")
    
    with tab_about:
        st.subheader("About StreamlitForge")
        
        st.markdown("""
        ### 🔨 StreamlitForge
        
        **Version:** 0.1.0
        
        An AI-Powered Streamlit Application Builder that helps you create
        beautiful, functional Streamlit applications with natural language.
        
        #### Features
        - 🤖 AI-powered code generation
        - 📁 Project management with automatic port assignment
        - 📚 Pattern learning from successful code
        - 🔑 Multi-provider LLM support
        - 🚀 One-click run
        
        #### Supported LLM Providers
        - **Ollama** (Free, Local)
        - **OpenAI** (GPT-4, GPT-3.5)
        - **Anthropic** (Claude)
        - **Groq** (Fast, Free Tier)
        - **Google** (Gemini)
        """)
        
        st.divider()
        st.caption("Built with ❤️ using Streamlit")


def test_ollama() -> bool:
    """Test Ollama connection."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        return resp.status_code == 200
    except:
        return False
