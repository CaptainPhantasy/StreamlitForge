"""Session state management for StreamlitForge."""

import streamlit as st
from pathlib import Path
import sys

_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

from streamlitforge.core.project_manager import ProjectManager
from streamlitforge.core.port_manager import PortManager
from streamlitforge.core.api_keys import APIKeyManager
from streamlitforge.knowledge.streamlit_kb import StreamlitKnowledgeBase
from streamlitforge.patterns.learner import PatternLearner


def init_session_state():
    """Initialize all session state variables."""
    
    # Core managers
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
    
    # Current state
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    
    if "selected_provider" not in st.session_state:
        st.session_state.selected_provider = "ollama"
    
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "🏠 Dashboard"
    
    # Chat/Builder state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "generated_code" not in st.session_state:
        st.session_state.generated_code = ""
    
    if "builder_agent" not in st.session_state:
        st.session_state.builder_agent = None
