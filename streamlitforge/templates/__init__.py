"""Template Engine for StreamlitForge project scaffolding."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.validation import validate_string, validate_dict


class TemplateError(Exception):
    """Base exception for template errors."""
    pass


class TemplateEngine:
    """Template engine for rendering StreamlitForge templates."""

    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize the template engine.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = Path(templates_dir) if templates_dir else None
        self._template_cache: Dict[str, str] = {}

    def load_template(self, name: str, category: str = 'project') -> str:
        """Load a template from the filesystem.

        Args:
            name: Template name
            category: Category of template ('project' or 'component')

        Returns:
            Template content as string

        Raises:
            TemplateError: If template cannot be loaded
        """
        if not self.templates_dir:
            raise TemplateError("Template directory not configured")

        template_path = self.templates_dir / category / f"{name}.j2"

        if not template_path.exists():
            raise TemplateError(f"Template not found: {template_path}")

        if name in self._template_cache:
            return self._template_cache[name]

        try:
            content = template_path.read_text(encoding='utf-8')
            self._template_cache[name] = content
            return content
        except Exception as e:
            raise TemplateError(f"Failed to load template {name}: {e}")

    def render(self, template_name: str, context: Dict[str, Any],
               category: str = 'project') -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template to render
            context: Dictionary of context variables
            category: Category of template

        Returns:
            Rendered template content

        Raises:
            TemplateError: If rendering fails
        """
        import jinja2

        try:
            template = self.load_template(template_name, category)
            return jinja2.Template(template).render(**context)
        except jinja2.TemplateError as e:
            raise TemplateError(f"Template rendering error: {e}")
        except Exception as e:
            raise TemplateError(f"Failed to render template {template_name}: {e}")

    def list_templates(self, category: str = 'project') -> List[str]:
        """List available templates in a category.

        Args:
            category: Category to list templates from

        Returns:
            List of template names
        """
        if not self.templates_dir:
            return []

        category_path = self.templates_dir / category

        if not category_path.exists() or not category_path.is_dir():
            return []

        templates = []
        for template_file in category_path.glob('*.j2'):
            templates.append(template_file.stem)

        return sorted(templates)

    def create_project_from_template(
        self,
        template_name: str,
        project_path: Path,
        context: Optional[Dict[str, Any]] = None,
        category: str = 'project'
    ) -> None:
        """Create a project from a template.

        Args:
            template_name: Name of the template to use
            project_path: Path where project should be created
            context: Dictionary of context variables
            category: Category of template
        """
        from ..utils.filesystem import create_directory, create_file

        context = context or {}

        # Render the main template
        try:
            content = self.render(template_name, context, category)
            main_file = project_path / "streamlit_app.py"
            create_file(str(main_file), content)

        except Exception as e:
            raise TemplateError(f"Failed to create project from template: {e}")

    def create_component_from_template(
        self,
        template_name: str,
        component_path: Path,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Create a component from a template.

        Args:
            template_name: Name of the template to use
            component_path: Path where component should be created
            context: Dictionary of context variables
        """
        from ..utils.filesystem import create_directory, create_file

        context = context or {}

        try:
            content = self.render(template_name, context, 'component')
            component_path.parent.mkdir(parents=True, exist_ok=True)
            create_file(str(component_path), content)

        except Exception as e:
            raise TemplateError(f"Failed to create component from template: {e}")


class BuiltInTemplates:
    """Built-in templates for StreamlitForge."""

    # Dashboard template
    DASHBOARD_TEMPLATE = '''import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard",
    page_icon="📊",
    layout="wide"
)

# Add title
st.title("Dashboard")

# Add description
st.markdown("""
This is a sample dashboard. Configure your data and visualizations here.
""")

# Example: Load data
@st.cache_data
def load_data():
    df = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=100),
        'Value': [i * 0.1 + (i % 10) for i in range(100)]
    })
    return df

# Load data
df = load_data()

# Add metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Value", f"{df['Value'].sum():.2f}")
with col2:
    st.metric("Average Value", f"{df['Value'].mean():.2f}")
with col3:
    st.metric("Maximum Value", f"{df['Value'].max():.2f}")

# Add charts
with st.expander("View Data"):
    st.dataframe(df)

chart_type = st.selectbox(
    "Chart Type",
    ["line", "bar", "scatter", "area"]
)

if chart_type == 'line':
    fig = px.line(df, x='Date', y='Value', title='Value Over Time')
elif chart_type == 'bar':
    fig = px.bar(df, x='Date', y='Value', title='Value Over Time')
elif chart_type == 'scatter':
    fig = px.scatter(df, x='Date', y='Value', title='Value Over Time')
else:
    fig = px.area(df, x='Date', y='Value', title='Value Over Time')

st.plotly_chart(fig, use_container_width=True)
'''

    # Chat template
    CHAT_TEMPLATE = '''import streamlit as st
import os
import requests

st.set_page_config(
    page_title="Chat",
    page_icon="💬",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Add title
st.title("Chat Interface")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type a message"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display thinking indicator
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

    # Generate response (replace with actual LLM call)
    response = generate_response(prompt)

    # Display response
    message_placeholder.markdown(response)

    # Add to history
    st.session_state.messages.append({"role": "assistant", "content": response})


def generate_response(prompt: str) -> str:
    """Generate a response from the LLM."""
    # TODO: Implement actual LLM integration
    return f"You said: {prompt}"
'''

    # CRUD template
    CRUD_TEMPLATE = '''import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="CRUD App",
    page_icon="📝",
    layout="wide"
)

st.title("CRUD Application")

# Add description
st.markdown("""
This is a sample CRUD application. Configure your data model and operations here.
""")

# Example: CRUD operations
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame({
        'id': [],
        'name': [],
        'email': [],
        'created_at': []
    })

data = st.session_state.data

# Add new item
with st.sidebar:
    st.header("Add New Item")
    name = st.text_input("Name")
    email = st.text_input("Email")

    if st.button("Add"):
        new_id = len(data) + 1
        data.loc[len(data)] = [new_id, name, email, datetime.now()]
        st.rerun()

# Display data
st.dataframe(data)

# Edit item
with st.sidebar:
    st.header("Edit Item")
    item_id = st.number_input("Item ID", min_value=1, value=1)

    if item_id > 0:
        row = data[data['id'] == item_id]
        if not row.empty:
            name = st.text_input("Name", value=row.iloc[0]['name'])
            email = st.text_input("Email", value=row.iloc[0]['email'])

            if st.button("Update"):
                data.loc[data['id'] == item_id, ['name', 'email']] = [name, email]
                st.rerun()

# Delete item
with st.sidebar:
    st.header("Delete Item")
    delete_id = st.number_input("Item ID to Delete", min_value=1, value=1)

    if st.button("Delete"):
        data = data[data['id'] != delete_id]
        st.session_state.data = data
        st.rerun()
'''

    # Analysis template
    ANALYSIS_TEMPLATE = '''import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats
import numpy as np

st.set_page_config(
    page_title="Analysis",
    page_icon="🔬",
    layout="wide"
)

st.title("Data Analysis Tool")

# Add description
st.markdown("""
This is a sample data analysis tool. Configure your analysis pipeline here.
""")

# Example: Upload and analyze data
uploaded_file = st.file_uploader("Upload Data", type=['csv', 'xlsx'])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("Data Preview")
    st.dataframe(df.head())

    # Add analysis options
    with st.sidebar:
        st.header("Analysis Options")

        target_col = st.selectbox("Target Column", df.columns)

        if target_col:
            st.subheader("Summary Statistics")
            st.write(df[target_col].describe())

            st.subheader("Correlation Matrix")
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            corr_matrix = df[numeric_cols].corr()
            st.dataframe(corr_matrix)

            st.subheader("Distribution Plot")
            fig = px.histogram(df, x=target_col, nbins=30)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Box Plot")
            fig = px.box(df, y=target_col)
            st.plotly_chart(fig, use_container_width=True)
'''

    # Admin template
    ADMIN_TEMPLATE = '''import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Admin Panel",
    page_icon="⚙️",
    layout="wide"
)

st.title("Admin Panel")

# Add description
st.markdown("""
This is a sample admin panel. Configure your dashboard here.
""")

# Example: Admin dashboard
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total_users': 1234,
        'active_users': 856,
        'new_signups_today': 23,
        'bounces': 45
    }

stats = st.session_state.stats

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Users", stats['total_users'], "+12%")

with col2:
    st.metric("Active Users", stats['active_users'], "+8%")

with col3:
    st.metric("New Signups Today", stats['new_signups_today'])

with col4:
    st.metric("Bounce Rate", f"{stats['bounces']}%", "-2%")

# User activity chart
st.subheader("User Activity")
st.line_chart([i for i in range(100)])

# Recent activity table
st.subheader("Recent Activity")
activity_data = pd.DataFrame({
    'User': ['User' + str(i) for i in range(1, 11)],
    'Action': ['Login', 'Sign up', 'Logout', 'Upload', 'Download'] * 2,
    'Time': ['10:00', '10:05', '10:10', '10:15', '10:20'] * 2
})
st.dataframe(activity_data)

# Quick actions
with st.sidebar:
    st.header("Quick Actions")
    if st.button("Generate Report"):
        st.toast("Report generated successfully!")
    if st.button("Clear Cache"):
        st.toast("Cache cleared!")
'''

    @classmethod
    def get_template(cls, name: str) -> str:
        """Get a built-in template by name.

        Args:
            name: Name of the template

        Returns:
            Template content

        Raises:
            TemplateError: If template not found
        """
        templates = {
            'dashboard': cls.DASHBOARD_TEMPLATE,
            'chat': cls.CHAT_TEMPLATE,
            'crud': cls.CRUD_TEMPLATE,
            'analysis': cls.ANALYSIS_TEMPLATE,
            'admin': cls.ADMIN_TEMPLATE
        }

        if name not in templates:
            raise TemplateError(f"Template not found: {name}")

        return templates[name]

    @classmethod
    def get_template_names(cls) -> list:
        """Get list of built-in template names.

        Returns:
            List of template names
        """
        return ['dashboard', 'chat', 'crud', 'analysis', 'admin']
