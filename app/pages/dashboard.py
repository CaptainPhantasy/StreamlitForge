"""Dashboard page for StreamlitForge."""

import streamlit as st
from pathlib import Path


def render():
    """Render the dashboard page."""
    
    st.title("🏠 Dashboard")
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        projects = st.session_state.project_manager.list_projects()
        st.metric("Projects", len(projects))
    
    with col2:
        providers = st.session_state.api_key_manager.list_providers()
        available = len([p for p, ok in providers.items() if ok])
        st.metric("AI Providers", available)
    
    with col3:
        patterns = st.session_state.pattern_learner.get_pattern_count()
        st.metric("Learned Patterns", patterns)
    
    with col4:
        components = st.session_state.knowledge_base.get_all_components()
        st.metric("Knowledge Items", len(components))
    
    st.divider()
    
    # Quick Actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🆕 New Project", use_container_width=True, type="primary"):
            st.session_state.active_tab = "📁 Projects"
            st.rerun()
    
    with col2:
        if st.button("🤖 Start Building", use_container_width=True):
            st.session_state.active_tab = "🤖 AI Builder"
            st.rerun()
    
    with col3:
        if st.button("📚 Browse Patterns", use_container_width=True):
            st.session_state.active_tab = "📚 Knowledge"
            st.rerun()
    
    st.divider()
    
    # Current Project Status
    if st.session_state.current_project:
        st.subheader("Current Project")
        
        project = st.session_state.current_project
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"### {project.get('name', 'Untitled')}")
                st.caption(f"📁 {project.get('path', 'No path')}")
            
            with col2:
                port = project.get('port', 'Not set')
                st.metric("Port", port)
            
            if st.button("Open in AI Builder", type="primary"):
                st.session_state.active_tab = "🤖 AI Builder"
                st.rerun()
    
    # Recent Projects
    st.subheader("Recent Projects")
    
    if projects:
        for project in projects[:5]:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"**{project.get('name', 'Untitled')}**")
                    st.caption(project.get('path', '')[:50] + "...")
                
                with col2:
                    st.caption(f"Port: {project.get('port', 'N/A')}")
                
                with col3:
                    if st.button("Select", key=f"select_{project.get('path', '')}"):
                        st.session_state.current_project = project
                        st.rerun()
    else:
        st.info("No projects yet. Create your first project to get started!")
    
    st.divider()
    
    # LLM Provider Status
    st.subheader("LLM Provider Status")
    
    providers = st.session_state.api_key_manager.list_providers()
    cols = st.columns(len(providers))
    
    for idx, (provider, available) in enumerate(providers.items()):
        with cols[idx]:
            icon = "✅" if available else "❌"
            st.metric(provider.capitalize(), icon)
    
    if not any(providers.values()):
        st.warning("No LLM providers configured. Go to Settings to add API keys.")
