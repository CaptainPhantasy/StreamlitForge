"""Knowledge Base page."""

import streamlit as st


def render():
    """Render the Knowledge Base page."""
    
    st.title("📚 Knowledge Base")
    
    # Tabs for different knowledge sources
    tab_components, tab_patterns, tab_docs = st.tabs([
        "Streamlit Components",
        "Learned Patterns",
        "Documentation",
    ])
    
    with tab_components:
        st.subheader("Streamlit Components Reference")
        
        kb = st.session_state.knowledge_base
        try:
            features = kb.get_latest_features()
            components = features.get("features", []) if features else []
        except:
            components = []
        
        if components:
            search = st.text_input("🔍 Search components", placeholder="e.g., chart, dataframe")
            
            filtered = components
            if search:
                search_lower = search.lower()
                filtered = [c for c in components if search_lower in str(c).lower()]
            
            for comp in filtered[:20]:
                with st.expander(f"📦 {comp if isinstance(comp, str) else comp.get('name', 'Unknown')}"):
                    st.markdown(str(comp) if isinstance(comp, str) else comp.get("description", "No description"))
        else:
            st.info("Component reference loaded. Features will display when available.")
            
            # Show built-in examples
            st.markdown("### Quick Reference")
            examples = [
                ("st.title()", "Main page title"),
                ("st.sidebar", "Sidebar for controls"),
                ("st.columns()", "Multi-column layout"),
                ("st.dataframe()", "Interactive data table"),
                ("st.line_chart()", "Line chart visualization"),
                ("st.chat_input()", "Chat input widget"),
            ]
            for cmd, desc in examples:
                st.code(f"{cmd}  # {desc}")
    
    with tab_patterns:
        st.subheader("Learned Patterns")
        
        learner = st.session_state.pattern_learner
        try:
            patterns = learner.list_patterns()
        except:
            patterns = []
        
        if patterns:
            for pattern in patterns:
                with st.expander(f"📝 {pattern.get('name', 'Pattern')}", expanded=False):
                    st.caption(pattern.get("description", ""))
                    if pattern.get("template"):
                        st.code(pattern.get("template"), language="python")
        else:
            st.info("No patterns learned yet. Patterns are saved from successful code generations.")
            
            st.markdown("### How Patterns Work")
            st.markdown("""
            Patterns are automatically learned when you:
            - Generate code that you save to a project
            - Mark generated code as helpful
            - Use similar code structures repeatedly
            
            Over time, StreamlitForge will build a library of reusable patterns.
            """)
    
    with tab_docs:
        st.subheader("Streamlit Documentation")
        
        st.markdown("""
        ### Quick Links
        
        - 📖 [Streamlit Documentation](https://docs.streamlit.io/)
        - 🎯 [API Reference](https://docs.streamlit.io/library/api-reference)
        - 💡 [Gallery](https://streamlit.io/gallery)
        """)
        
        st.markdown("### Common Patterns")
        
        common_patterns = [
            ("Page Config", """st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
)"""),
            ("Sidebar Layout", """with st.sidebar:
    st.header("Settings")
    option = st.selectbox("Choose", ["A", "B"])"""),
            ("Two Columns", """col1, col2 = st.columns(2)
with col1:
    st.metric("Sales", "$1.2M", "+12%")
with col2:
    st.metric("Users", "45K", "+5%")"""),
            ("Data Display", """import pandas as pd
df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
st.dataframe(df)
st.line_chart(df)"""),
            ("Session State", """if "count" not in st.session_state:
    st.session_state.count = 0
if st.button("Increment"):
    st.session_state.count += 1"""),
        ]
        
        for name, code in common_patterns:
            with st.expander(f"📝 {name}"):
                st.code(code, language="python")
