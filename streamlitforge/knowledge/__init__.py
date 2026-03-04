"""Streamlit Knowledge Base for documentation and examples."""

from typing import Any, Dict, List, Optional

from ..utils.validation import validate_string, validate_bool


class KnowledgeError(Exception):
    """Base exception for knowledge base errors."""
    pass


class KnowledgeBase:
    """Knowledge base for Streamlit documentation and examples."""

    def __init__(self, docs_url: str = 'https://docs.streamlit.io',
                 max_examples: int = 10, embedding_dim: int = 384):
        """Initialize the knowledge base.

        Args:
            docs_url: URL to Streamlit documentation
            max_examples: Maximum number of examples to store
            embedding_dim: Embedding dimension for vector search
        """
        self.docs_url = docs_url
        self.max_examples = max_examples
        self.embedding_dim = embedding_dim

        # Store examples and patterns
        self.examples: List[Dict[str, Any]] = []
        self.patterns: List[Dict[str, Any]] = []
        self.embeddings: Dict[str, List[float]] = {}

    def add_example(self, title: str, content: str, category: str = 'general',
                    tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Add an example to the knowledge base.

        Args:
            title: Example title
            content: Example code or content
            category: Category of the example
            tags: Optional tags for the example

        Returns:
            The added example dictionary
        """
        example = {
            'id': self._generate_id(),
            'title': validate_string(title),
            'content': content,
            'category': validate_string(category),
            'tags': tags or [],
            'created_at': None
        }

        # Implement embedding generation
        example['embedding'] = self._generate_embedding(content)

        self.examples.append(example)

        if len(self.examples) > self.max_examples:
            self.examples.pop(0)

        return example

    def search_examples(self, query: str, category: Optional[str] = None,
                       limit: int = 5) -> List[Dict[str, Any]]:
        """Search examples using semantic similarity.

        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results

        Returns:
            List of matching examples
        """
        query_embedding = self._generate_embedding(query)

        scored_examples = []

        for example in self.examples:
            if category and example['category'] != category:
                continue

            # Simple similarity scoring (cosine similarity)
            similarity = self._cosine_similarity(query_embedding, example['embedding'])
            scored_examples.append((similarity, example))

        # Sort by similarity and return top results
        scored_examples.sort(key=lambda x: x[0], reverse=True)

        return [example for _, example in scored_examples[:limit]]

    def get_category_examples(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get examples by category.

        Args:
            category: Category name
            limit: Maximum number of examples

        Returns:
            List of examples in the category
        """
        category_examples = [
            ex for ex in self.examples
            if ex['category'] == category
        ]

        return category_examples[:limit]

    def add_pattern(self, name: str, pattern: Dict[str, Any], tags: List[str] = None) -> Dict[str, Any]:
        """Add a pattern to the knowledge base.

        Args:
            name: Pattern name
            pattern: Pattern dictionary with structure and usage
            tags: Optional tags for the pattern

        Returns:
            The added pattern dictionary
        """
        if not pattern.get('template'):
            raise KnowledgeError("Pattern must have a template")

        pattern_entry = {
            'id': self._generate_id(),
            'name': validate_string(name),
            'template': pattern.get('template', ''),
            'description': pattern.get('description', ''),
            'structure': pattern.get('structure', {}),
            'usage': pattern.get('usage', ''),
            'tags': tags or [],
            'category': pattern.get('category', 'general'),
            'created_at': None
        }

        self.patterns.append(pattern_entry)
        return pattern_entry

    def get_pattern(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by name.

        Args:
            name: Pattern name

        Returns:
            Pattern dictionary or None
        """
        for pattern in self.patterns:
            if pattern['name'] == name:
                return pattern
        return None

    def search_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search patterns using semantic similarity.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching patterns
        """
        query_embedding = self._generate_embedding(query)

        scored_patterns = []

        for pattern in self.patterns:
            # Use template and description for embedding
            content = f"{pattern['template']} {pattern['description']}"
            pattern_embedding = self._generate_embedding(content)

            similarity = self._cosine_similarity(query_embedding, pattern_embedding)
            scored_patterns.append((similarity, pattern))

        scored_patterns.sort(key=lambda x: x[0], reverse=True)

        return [pattern for _, pattern in scored_patterns[:limit]]

    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get patterns by category.

        Args:
            category: Category name

        Returns:
            List of patterns in the category
        """
        return [
            pattern for pattern in self.patterns
            if pattern['category'] == category
        ]

    def get_patterns_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get patterns by tag.

        Args:
            tag: Tag name

        Returns:
            List of patterns with the tag
        """
        return [
            pattern for pattern in self.patterns
            if tag in pattern['tags']
        ]

    def get_streamlit_docs_url(self) -> str:
        """Get the Streamlit documentation URL.

        Returns:
            Documentation URL
        """
        return self.docs_url

    def get_example_count(self, category: Optional[str] = None) -> int:
        """Get the number of examples.

        Args:
            category: Optional category filter

        Returns:
            Number of examples
        """
        if category:
            return len([ex for ex in self.examples if ex['category'] == category])
        return len(self.examples)

    def get_pattern_count(self, category: Optional[str] = None) -> int:
        """Get the number of patterns.

        Args:
            category: Optional category filter

        Returns:
            Number of patterns
        """
        if category:
            return len([p for p in self.patterns if p['category'] == category])
        return len(self.patterns)

    def _generate_id(self) -> str:
        """Generate a unique identifier.

        Returns:
            Unique ID string
        """
        import hashlib
        import uuid

        unique_id = uuid.uuid4().hex
        return hashlib.md5(unique_id.encode()).hexdigest()

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding as list of floats
        """
        # In a real implementation, this would use an embedding model
        # For now, return a simple hash-based embedding
        import hashlib
        import numpy as np

        # Simple hash-based embedding (replace with real embedding in production)
        hash_val = int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)
        embedding = np.array([hash_val % 256] * self.embedding_dim, dtype=float)

        return embedding.tolist()

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score
        """
        import numpy as np

        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class BuiltInKnowledgeBase(KnowledgeBase):
    """Knowledge base with built-in Streamlit examples and patterns."""

    def __init__(self, **kwargs):
        """Initialize the built-in knowledge base."""
        super().__init__(**kwargs)
        self._load_builtins()

    def _load_builtins(self) -> None:
        """Load built-in examples and patterns."""
        # Add built-in examples
        self.add_example(
            title="Basic Chat Interface",
            content="""import streamlit as st

st.title("Chat Interface")

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Say something"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        response = llm.generate(prompt)
        message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
""",
            category="chat",
            tags=["chat", "llm", "conversation"]
        )

        self.add_example(
            title="Data Visualization Dashboard",
            content="""import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Dashboard")

uploaded_file = st.file_uploader("Upload data", type=['csv'])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)

    with st.sidebar:
        chart_type = st.selectbox("Chart Type", ["line", "bar", "scatter"])

    if chart_type == 'line':
        fig = px.line(df, x=df.columns[0], y=df.columns[1])
    elif chart_type == 'bar':
        fig = px.bar(df, x=df.columns[0], y=df.columns[1])
    else:
        fig = px.scatter(df, x=df.columns[0], y=df.columns[1])

    st.plotly_chart(fig, use_container_width=True)
""",
            category="visualization",
            tags=["dashboard", "charts", "plotly"]
        )

        self.add_example(
            title="Multi-Page Application",
            content="""# app.py
import streamlit as st

st.set_page_config(
    page_title="Multi-Page App",
    page_icon="🚀",
    layout="wide"
)

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Home", "About", "Contact"]
)

if page == "Home":
    st.title("Home Page")
    st.write("Welcome to the home page!")

elif page == "About":
    st.title("About")
    st.write("This is a multi-page application.")

elif page == "Contact":
    st.title("Contact")
    st.write("Get in touch with us!")
""",
            category="multi-page",
            tags=["multi-page", "navigation"]
        )

        # Add built-in patterns
        self.add_pattern(
            name="chat-ui-pattern",
            pattern={
                'template': '''import streamlit as st

st.title("Chat Interface")

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type a message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        response = llm.generate(prompt)
        message_placeholder.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
''',
                'description': 'Standard chat interface pattern with message history',
                'structure': {
                    'session_state': 'Store messages in st.session_state',
                    'user_message': 'Display user message',
                    'assistant_response': 'Generate and display response'
                },
                'usage': 'Use this pattern for LLM-powered chat applications',
                'category': 'ui'
            },
            tags=["chat", "llm", "ui-pattern"]
        )

        self.add_pattern(
            name="dashboard-layout-pattern",
            pattern={
                'template': '''import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

with st.sidebar:
    filter_options = st.selectbox("Filter", ["All", "Option1", "Option2"])

data = load_data()

st.title("Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total", len(data))

with col2:
    st.metric("Average", data["value"].mean())

fig = px.line(data, x="date", y="value")
st.plotly_chart(fig, use_container_width=True)
''',
                'description': 'Layout pattern for data dashboards',
                'structure': {
                    'sidebar': 'Filters and controls',
                    'columns': 'Grid layout for metrics',
                    'charts': 'Visualization area'
                },
                'usage': 'Use this pattern for analytics dashboards',
                'category': 'ui'
            },
            tags=["dashboard", "layout", "charts"]
        )
