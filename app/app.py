"""StreamlitForge - AI-Powered Streamlit Application Builder.

A visual GUI for building Streamlit applications with AI assistance.
"""

import streamlit as st
from pathlib import Path
import sys
import os

# Get the project root directory
_APP_DIR = Path(__file__).parent.resolve()
_ROOT_DIR = _APP_DIR.parent

# Add to path
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

os.chdir(_ROOT_DIR)

from streamlitforge.core.project_manager import ProjectManager
from streamlitforge.core.port_manager import PortManager
from streamlitforge.core.api_keys import APIKeyManager
from streamlitforge.knowledge.streamlit_kb import StreamlitKnowledgeBase
from streamlitforge.patterns.learner import PatternLearner


def init_session_state():
    """Initialize all session state variables."""
    if "project_manager" not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    if "port_manager" not in st.session_state:
        st.session_state.port_manager = PortManager()
    if "api_key_manager" not in st.session_state:
        st.session_state.api_key_manager = APIKeyManager()
    if "knowledge_base" not in st.session_state:
        st.session_state.knowledge_base = StreamlitKnowledgeBase()
    if "pattern_learner" not in st.session_state:
        st.session_state.pattern_learner = PatternLearner()
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = "ollama"
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "🏠 Dashboard"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "generated_code" not in st.session_state:
        st.session_state.generated_code = ""
    if "builder_agent" not in st.session_state:
        st.session_state.builder_agent = None


def render_dashboard():
    """Render the dashboard page."""
    st.title("🏠 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    projects = st.session_state.project_manager.list_projects()
    configured = st.session_state.api_key_manager.list_configured()
    
    # Get pattern counts
    pattern_learner = st.session_state.pattern_learner
    builtin_patterns = pattern_learner.get_builtin_pattern_count() if hasattr(pattern_learner, 'get_builtin_pattern_count') else 0
    total_patterns = pattern_learner.get_pattern_count()
    
    with col1:
        st.metric("Projects", len(projects))
    with col2:
        st.metric("AI Providers", len(configured))
    with col3:
        st.metric("Patterns", f"{total_patterns}", f"{builtin_patterns} built-in")
    with col4:
        st.metric("Status", "Ready")
    
    st.divider()
    
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🆕 New Project", use_container_width=True, type="primary"):
            st.session_state.active_tab = "📁 Projects"
            st.rerun()
    with col2:
        if st.button("🚀 Start Building", use_container_width=True, type="primary"):
            st.session_state.active_tab = "🤖 AI Builder"
            st.rerun()
    with col3:
        if st.button("📚 Browse Knowledge", use_container_width=True):
            st.session_state.active_tab = "📚 Knowledge"
            st.rerun()
    
    st.divider()
    
    if st.session_state.current_project:
        st.subheader("Current Project")
        project = st.session_state.current_project
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {project.get('name', 'Untitled')}")
                st.caption(f"📁 {project.get('path', 'No path')}")
            with col2:
                st.metric("Port", project.get('port', 'Not set'))
    
    st.subheader("Recent Projects")
    if projects:
        for project in projects[:5]:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{project.get('name', 'Untitled')}**")
                with col2:
                    st.caption(f"Port: {project.get('port', 'N/A')}")
                with col3:
                    if st.button("Select", key=f"sel_{project.get('path', '')}"):
                        st.session_state.current_project = project
                        st.rerun()
    else:
        st.info("No projects yet. Create your first project to get started!")
    
    st.divider()
    
    st.subheader("LLM Provider Status")
    all_providers = ["openai", "anthropic", "groq", "google", "ollama", "openrouter", "opencode"]
    cols = st.columns(len(all_providers))
    for idx, provider in enumerate(all_providers):
        with cols[idx]:
            icon = "✅" if provider in configured or provider == "ollama" else "❌"
            st.metric(provider.capitalize(), icon)


# Page configuration
st.set_page_config(
    page_title="StreamlitForge",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
init_session_state()

# Sidebar
with st.sidebar:
    st.title("🔨 StreamlitForge")
    st.caption("AI-Powered Streamlit Builder")
    st.divider()
    
    st.subheader("📁 Project")
    projects = st.session_state.project_manager.list_projects()
    project_names = [p.get("name", "Untitled") for p in projects]
    
    if project_names:
        selected = st.selectbox("Select Project", project_names, label_visibility="collapsed")
        if selected:
            for p in projects:
                if p.get("name") == selected:
                    st.session_state.current_project = p
                    break
    else:
        st.info("No projects yet")
    
    with st.expander("+ New Project"):
        new_name = st.text_input("Project Name", key="new_project_name")
        new_path = st.text_input("Path", value=str(Path.home() / "streamlit_projects"), key="new_project_path")
        if st.button("Create", use_container_width=True):
            if new_name:
                try:
                    project_dir = st.session_state.project_manager.create_project(
                        project_name=new_name,
                        parent_dir=new_path,
                    )
                    st.success(f"Created {new_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    
    st.divider()
    
    st.subheader("🤖 AI Provider")
    configured = st.session_state.api_key_manager.list_configured()
    if configured:
        selected_provider = st.selectbox("Provider", configured, label_visibility="collapsed")
        st.session_state.selected_provider = selected_provider
    else:
        st.warning("No providers configured")
        if st.button("Setup API Keys"):
            st.session_state.active_tab = "⚙️ Settings"
    
    st.divider()
    
    st.subheader("Navigation")
    tabs = [
        "🏠 Dashboard",
        "🤖 AI Builder",
        "📁 Projects",
        "📚 Templates",
        "🔄 Converter",
        "🚀 Deployment",
        "🔌 MCP",
        "🤖 LLM Status",
        "📚 Knowledge",
        "⚙️ Settings",
    ]
    active_tab = st.radio(
        "Tabs", tabs,
        index=tabs.index(st.session_state.get("active_tab", "🏠 Dashboard")),
        label_visibility="collapsed",
    )
    st.session_state.active_tab = active_tab

# Main content
if active_tab == "🏠 Dashboard":
    render_dashboard()
elif active_tab == "🤖 AI Builder":
    from app.pages.builder import render
    render()
elif active_tab == "📁 Projects":
    from app.pages.projects import render
    render()
elif active_tab == "📚 Templates":
    from app.pages.templates import render
    render()
elif active_tab == "🔄 Converter":
    from app.pages.converter import render
    render()
elif active_tab == "🚀 Deployment":
    from app.pages.deployment import render
    render()
elif active_tab == "🔌 MCP":
    from app.pages.mcp import render
    render()
elif active_tab == "🤖 LLM Status":
    from app.pages.llm_status import render
    render()
elif active_tab == "📚 Knowledge":
    from app.pages.knowledge import render
    render()
elif active_tab == "⚙️ Settings":
    from app.pages.settings import render
    render()
