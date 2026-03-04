"""Template Browser page - Browse and select Streamlit templates."""

import streamlit as st
from pathlib import Path


def render():
    """Render the Template Browser page."""
    
    st.title("📚 Template Browser")
    
    st.markdown("""
    Browse built-in templates and select a starting point for your Streamlit application.
    """)
    
    # Import templates module
    from streamlitforge.templates import BuiltInTemplates, TemplateEngine
    
    # Template categories
    st.subheader("Template Categories")
    
    categories = {
        "Dashboard": {"icon": "📊", "desc": "Data visualization dashboards with charts and metrics"},
        "Chat": {"icon": "💬", "desc": "Chat interfaces with message history"},
        "CRUD": {"icon": "📝", "desc": "Create, Read, Update, Delete applications"},
        "Analysis": {"icon": "🔬", "desc": "Data analysis tools with statistical functions"},
        "Admin": {"icon": "⚙️", "desc": "Admin panels with user management and monitoring"},
    }
    
    # Category filter
    selected_category = st.pills(
        "Filter by category",
        options=["All"] + list(categories.keys()),
        default="All",
    )
    
    st.divider()
    
    # Built-in templates
    st.subheader("Built-in Templates")
    
    template_info = {
        "dashboard": {
            "name": "Dashboard Template",
            "icon": "📊",
            "category": "Dashboard",
            "features": ["Metrics display", "Plotly charts", "Data tables", "Expandable sections"],
        },
        "chat": {
            "name": "Chat Interface",
            "icon": "💬",
            "category": "Chat",
            "features": ["Message history", "Chat input", "Streaming support", "Role-based display"],
        },
        "crud": {
            "name": "CRUD Application",
            "icon": "📝",
            "category": "CRUD",
            "features": ["Add/Edit/Delete", "Form inputs", "Data table", "Session state"],
        },
        "analysis": {
            "name": "Data Analysis Tool",
            "icon": "🔬",
            "category": "Analysis",
            "features": ["File upload", "Statistics", "Visualizations", "Correlation analysis"],
        },
        "admin": {
            "name": "Admin Panel",
            "icon": "⚙️",
            "category": "Admin",
            "features": ["Metrics overview", "Activity feed", "Quick actions", "User management"],
        },
    }
    
    # Display templates
    for template_id, info in template_info.items():
        if selected_category != "All" and info["category"] != selected_category:
            continue
        
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"# {info['icon']}")
            
            with col2:
                st.markdown(f"### {info['name']}")
                st.caption(f"Category: {info['category']}")
                
                st.markdown("**Features:**")
                for feature in info["features"]:
                    st.caption(f"✅ {feature}")
            
            with col3:
                if st.button("Preview", key=f"preview_{template_id}", use_container_width=True):
                    st.session_state.preview_template = template_id
                    st.rerun()
                
                if st.button("Use", key=f"use_{template_id}", type="primary", use_container_width=True):
                    st.session_state.selected_template = template_id
                    if st.session_state.current_project:
                        apply_template(template_id, st.session_state.current_project)
                        st.success("Template applied!")
                    else:
                        st.warning("Select a project first")
        
        st.divider()
    
    # Template preview
    if "preview_template" in st.session_state:
        template_id = st.session_state.preview_template
        template_code = BuiltInTemplates.get_template(template_id)
        
        with st.modal(f"Preview: {template_info[template_id]['name']}", max_width="large"):
            st.code(template_code, language="python")
            
            if st.button("Use This Template", type="primary"):
                st.session_state.selected_template = template_id
                if st.session_state.current_project:
                    apply_template(template_id, st.session_state.current_project)
                    st.success("Template applied to current project!")
                del st.session_state.preview_template
                st.rerun()
            
            if st.button("Close"):
                del st.session_state.preview_template
                st.rerun()
    
    # Component templates
    st.divider()
    st.subheader("Component Snippets")
    
    component_tabs = st.tabs(["Charts", "Forms", "Tables"])
    
    with component_tabs[0]:
        st.markdown("#### Chart Components")
        
        chart_snippets = {
            "Line Chart": '''import plotly.express as px
fig = px.line(df, x='date', y='value', title='Trend')
st.plotly_chart(fig, use_container_width=True)''',
            "Bar Chart": '''import plotly.express as px
fig = px.bar(df, x='category', y='value', title='Comparison')
st.plotly_chart(fig, use_container_width=True)''',
            "Pie Chart": '''import plotly.express as px
fig = px.pie(df, values='value', names='category', title='Distribution')
st.plotly_chart(fig, use_container_width=True)''',
        }
        
        for name, code in chart_snippets.items():
            with st.expander(f"📊 {name}"):
                st.code(code, language="python")
                if st.button("Copy", key=f"copy_chart_{name}"):
                    st.session_state.clipboard = code
                    st.success("Copied!")
    
    with component_tabs[1]:
        st.markdown("#### Form Components")
        
        form_snippets = {
            "Login Form": '''with st.form("login"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")
    if submitted:
        # Handle login
        pass''',
            "Settings Form": '''with st.form("settings"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    notifications = st.checkbox("Enable notifications")
    submitted = st.form_submit_button("Save Settings")''',
        }
        
        for name, code in form_snippets.items():
            with st.expander(f"📝 {name}"):
                st.code(code, language="python")
    
    with component_tabs[2]:
        st.markdown("#### Table Components")
        
        table_snippets = {
            "Editable Table": '''edited_df = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
)''',
            "Formatted Table": '''st.dataframe(
    df.style.highlight_max(axis=0),
    column_config={
        "price": st.column_config.NumberColumn("Price ($)", format="$%.2f"),
        "date": st.column_config.DateColumn("Date"),
    }
)''',
        }
        
        for name, code in table_snippets.items():
            with st.expander(f"📋 {name}"):
                st.code(code, language="python")
    
    # Custom templates
    st.divider()
    
    with st.expander("📁 Custom Templates"):
        st.markdown("""
        You can create custom templates by adding `.j2` files to:
        
        ```
        ~/.streamlitforge/templates/projects/
        ~/.streamlitforge/templates/components/
        ```
        
        Templates use Jinja2 syntax with these variables:
        - `{{ project_name }}` - The project name
        - `{{ port }}` - The assigned port
        - `{{ features }}` - List of enabled features
        """)
        
        # Show template directory
        template_dir = Path.home() / ".streamlitforge" / "templates"
        if template_dir.exists():
            st.markdown("**Your Templates:**")
            for f in template_dir.glob("**/*.j2"):
                st.caption(f"📄 {f.relative_to(template_dir)}")
        else:
            st.info("No custom templates yet. Create the directory above to add your own.")


def apply_template(template_id: str, project: dict):
    """Apply a template to the current project."""
    from streamlitforge.templates import BuiltInTemplates
    from pathlib import Path
    
    template_code = BuiltInTemplates.get_template(template_id)
    
    if project:
        project_path = Path(project.get("path", ""))
        app_file = project_path / "src" / "app.py"
        
        app_file.parent.mkdir(parents=True, exist_ok=True)
        app_file.write_text(template_code)
        
        # Also update session state
        st.session_state.generated_code = template_code
