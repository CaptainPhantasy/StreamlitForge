"""MCP Integration page - Control Floyd Labs MCP ecosystem integration."""

import streamlit as st


def render():
    """Render the MCP Integration page."""
    
    st.title("🔌 MCP Integration")
    
    st.markdown("""
    StreamlitForge integrates with the Floyd Labs MCP (Model Context Protocol) ecosystem
    for enhanced capabilities including caching, safe operations, code analysis, and pattern learning.
    """)
    
    # Import MCP module
    from streamlitforge.mcp_integration import (
        StreamlitForgeMCPIntegration,
        MCPLabClient,
    )
    
    # MCP endpoint configuration
    st.subheader("MCP Server Configuration")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        endpoint = st.text_input(
            "MCP Endpoint",
            value=st.session_state.get("mcp_endpoint", "http://localhost:8108/mcp"),
            help="The URL of the MCP gateway server",
        )
        st.session_state.mcp_endpoint = endpoint
    
    with col2:
        if st.button("Test Connection", use_container_width=True):
            client = MCPLabClient(endpoint)
            if client.is_available():
                st.session_state.mcp_available = True
                st.success("✅ Connected!")
            else:
                st.session_state.mcp_available = False
                st.error("❌ Cannot connect")
    
    # Initialize integration
    mcp = StreamlitForgeMCPIntegration(endpoint)
    is_available = mcp.is_available()
    
    st.divider()
    
    # Status dashboard
    st.subheader("Service Status")
    
    services = [
        ("Supercache", "Pattern storage and caching", "supercache"),
        ("Safe Ops", "Safe code modifications", "safe_ops"),
        ("DevTools", "Code analysis and test generation", "devtools"),
        ("Context Singularity", "Code indexing and search", "context"),
        ("Pattern Crystallizer", "Pattern learning and adaptation", "patterns"),
    ]
    
    cols = st.columns(len(services))
    
    for idx, (name, desc, attr) in enumerate(services):
        with cols[idx]:
            status_icon = "🟢" if is_available else "🔴"
            st.metric(name, status_icon)
            st.caption(desc)
    
    st.divider()
    
    # Service-specific controls
    if is_available:
        tab_supercache, tab_safeops, tab_devtools, tab_context, tab_patterns = st.tabs([
            "📦 Supercache", "🛡️ Safe Ops", "🔧 DevTools", "🔍 Context", "✨ Patterns"
        ])
        
        with tab_supercache:
            st.subheader("Supercache Integration")
            st.markdown("Store and retrieve patterns, reasoning chains, and code snippets.")
            
            # Search patterns
            search_query = st.text_input("Search Patterns", placeholder="Enter search query...")
            if st.button("Search", key="search_supercache"):
                try:
                    results = mcp.supercache.search(search_query, tier="all")
                    if results:
                        st.success(f"Found {len(results)} results")
                        for r in results[:5]:
                            with st.container(border=True):
                                st.markdown(f"**{r.get('name', 'Unnamed')}**")
                                st.caption(r.get('summary', '')[:200])
                    else:
                        st.info("No results found")
                except Exception as e:
                    st.error(f"Search failed: {e}")
            
            st.divider()
            
            # Store pattern
            with st.expander("Store New Pattern"):
                pattern_name = st.text_input("Pattern Name", key="pattern_name")
                pattern_code = st.text_area("Pattern Code", height=150, key="pattern_code")
                pattern_tags = st.text_input("Tags (comma-separated)", key="pattern_tags")
                
                if st.button("Store Pattern", type="primary"):
                    if pattern_name and pattern_code:
                        try:
                            key = mcp.supercache.store_pattern(
                                pattern_name,
                                {"code": pattern_code},
                                pattern_tags.split(",") if pattern_tags else [],
                            )
                            st.success(f"Stored with key: {key}")
                        except Exception as e:
                            st.error(f"Failed to store: {e}")
                    else:
                        st.warning("Name and code required")
        
        with tab_safeops:
            st.subheader("Safe Ops Integration")
            st.markdown("Perform safe code modifications with impact simulation.")
            
            st.info("Safe Ops requires a target project and operations list.")
            
            # Simulate impact
            with st.expander("Simulate Impact"):
                st.markdown("""
                Define operations to simulate their impact before applying:
                """)
                
                st.code('''operations = [
    {"type": "replace", "file": "app.py", "old": "old_code", "new": "new_code"},
    {"type": "insert", "file": "utils.py", "line": 10, "content": "new_line"},
]''', language="python")
                
                if st.session_state.current_project:
                    if st.button("Run Simulation"):
                        try:
                            result = mcp.safe_ops.simulate_impact(
                                [],  # operations
                                st.session_state.current_project.get("path", ""),
                            )
                            st.json(result)
                        except Exception as e:
                            st.error(f"Simulation failed: {e}")
                else:
                    st.warning("Select a project first")
        
        with tab_devtools:
            st.subheader("DevTools Integration")
            st.markdown("Code analysis and test generation.")
            
            # Dependency analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Dependency Analysis")
                if st.session_state.current_project:
                    if st.button("Analyze Dependencies"):
                        try:
                            result = mcp.devtools.analyze_dependencies(
                                st.session_state.current_project.get("path", "")
                            )
                            st.json(result)
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")
                else:
                    st.info("Select a project first")
            
            with col2:
                st.markdown("#### Test Generation")
                source_code = st.text_area("Source Code", height=100, key="devtools_source")
                framework = st.selectbox("Framework", ["pytest", "unittest", "nose"])
                
                if st.button("Generate Tests"):
                    if source_code:
                        try:
                            tests = mcp.devtools.generate_tests(source_code, framework)
                            st.code(tests, language="python")
                        except Exception as e:
                            st.error(f"Generation failed: {e}")
                    else:
                        st.warning("Enter source code")
        
        with tab_context:
            st.subheader("Context Singularity Integration")
            st.markdown("Code indexing and semantic search.")
            
            # Index project
            if st.session_state.current_project:
                if st.button("Index Project"):
                    try:
                        with st.spinner("Indexing..."):
                            result = mcp.context.ingest(
                                st.session_state.current_project.get("path", ""),
                                "**/*.py"
                            )
                        st.success("Project indexed!")
                        st.json(result)
                    except Exception as e:
                        st.error(f"Indexing failed: {e}")
            
            st.divider()
            
            # Search code
            search_query = st.text_input("Search Code", key="context_search")
            if st.button("Search", key="context_search_btn"):
                if search_query:
                    try:
                        results = mcp.context.search(search_query, limit=10)
                        for r in results:
                            with st.container(border=True):
                                st.markdown(f"**{r.get('file', 'Unknown')}**")
                                st.code(r.get('content', '')[:500], language="python")
                    except Exception as e:
                        st.error(f"Search failed: {e}")
        
        with tab_patterns:
            st.subheader("Pattern Crystallizer Integration")
            st.markdown("Learn and adapt patterns from successful code.")
            
            # Detect patterns
            code_input = st.text_area("Code to Analyze", height=150, key="pattern_code_input")
            context_desc = st.text_input("Context Description", key="pattern_context")
            
            if st.button("Detect & Crystallize"):
                if code_input:
                    try:
                        result = mcp.patterns.detect_and_crystallize(
                            code_input,
                            context_desc,
                            ["streamlit", "ui"],
                        )
                        st.success("Pattern detected and crystallized!")
                        st.json(result)
                    except Exception as e:
                        st.error(f"Detection failed: {e}")
                else:
                    st.warning("Enter code to analyze")
            
            st.divider()
            
            # Adapt pattern
            adapt_query = st.text_input("Describe what you need", key="adapt_query")
            if st.button("Find Similar Patterns"):
                if adapt_query:
                    try:
                        patterns = mcp.patterns.adapt_pattern(adapt_query, "streamlit app")
                        if patterns:
                            for p in patterns:
                                with st.container(border=True):
                                    st.markdown(f"**{p.get('name', 'Pattern')}**")
                                    st.code(p.get('code', ''), language="python")
                        else:
                            st.info("No similar patterns found")
                    except Exception as e:
                        st.error(f"Search failed: {e}")
    
    else:
        st.warning("⚠️ MCP server is not available. Start the MCP gateway to enable integrations.")
        
        with st.expander("How to start MCP server"):
            st.code("""# Start the MCP gateway server
floyd-mcp-gateway start --port 8108

# Or using Docker
docker run -p 8108:8108 floyd/mcp-gateway:latest""", language="bash")
        
        # Show offline capabilities
        st.info("StreamlitForge will use local fallbacks when MCP is unavailable:")
        st.markdown("""
        - **Pattern Library**: Local pattern storage
        - **Caching**: In-memory caching
        - **Code Analysis**: Basic AST parsing
        """)
