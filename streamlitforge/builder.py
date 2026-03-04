"""Interactive App Builder — Streamlit chat-based interface."""

from typing import Any, Dict, List, Optional


class ConversationManager:
    """Manages chat conversation state and context."""

    def __init__(self, max_context_messages: int = 20):
        self.max_context = max_context_messages
        self.messages: List[Dict[str, str]] = []
        self.mode: str = "chat"

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_context * 2:
            self.messages = self.messages[-self.max_context:]

    def get_context(self) -> List[Dict[str, str]]:
        return self.messages[-self.max_context:]

    def set_mode(self, mode: str):
        if mode in ("chat", "build", "expert"):
            self.mode = mode

    def clear(self):
        self.messages.clear()


class CodePreviewManager:
    """Manages code extraction and preview from assistant responses."""

    def __init__(self):
        self.code_blocks: List[str] = []

    def extract_code(self, content: str) -> List[str]:
        import re
        blocks = re.findall(r"```(?:python)?\n(.*?)```", content, re.DOTALL)
        self.code_blocks.extend(blocks)
        return blocks

    def get_latest_code(self) -> Optional[str]:
        return self.code_blocks[-1] if self.code_blocks else None

    def clear(self):
        self.code_blocks.clear()


class InteractiveBuilder:
    """Chat-based Streamlit app builder with multiple modes."""

    MODES = {
        "chat": "Chat Mode — Q&A, Help, and Learning",
        "build": "Build Mode — Code Generation",
        "expert": "Expert Mode — Senior Developer Guidance",
    }

    BUILD_SYSTEM_PROMPT = """You are StreamlitForge Builder, an expert at generating
clean, idiomatic Streamlit code. Generate only the code needed, with brief
explanations. Follow Streamlit best practices."""

    CHAT_SYSTEM_PROMPT = """You are StreamlitForge Assistant, helping users learn
and use Streamlit effectively. Provide clear explanations with code examples
when appropriate."""

    def __init__(self):
        self.conversation = ConversationManager()
        self.code_preview = CodePreviewManager()

    def get_system_prompt(self, mode: str = None) -> str:
        mode = mode or self.conversation.mode
        if mode == "build":
            return self.BUILD_SYSTEM_PROMPT
        elif mode == "expert":
            from .persona import SENIOR_DEVELOPER_PROMPT
            return SENIOR_DEVELOPER_PROMPT
        return self.CHAT_SYSTEM_PROMPT

    def process_input(self, user_input: str, mode: str = None) -> Dict[str, Any]:
        mode = mode or self.conversation.mode
        self.conversation.add_message("user", user_input)
        return {
            "mode": mode,
            "system_prompt": self.get_system_prompt(mode),
            "messages": self.conversation.get_context(),
            "temperature": 0.3 if mode == "build" else 0.5 if mode == "expert" else 0.7,
        }

    def render_streamlit_ui(self):
        """Generate Streamlit app code for the builder UI."""
        return '''import streamlit as st

st.set_page_config(
    page_title="StreamlitForge Builder",
    page_icon="🔨",
    layout="wide"
)

mode = st.sidebar.radio(
    "Mode",
    ["💬 Chat", "🔧 Build", "🎓 Expert"],
    index=0
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me about Streamlit..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        st.write("Processing your request...")
'''
