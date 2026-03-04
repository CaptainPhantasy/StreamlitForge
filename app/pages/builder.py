"""AI Builder page - Main interface for building Streamlit apps with AI."""

import streamlit as st
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatMessage:
    """A chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    code: Optional[str] = None


class BuilderAgent:
    """AI agent for building Streamlit applications."""
    
    def __init__(self, provider: str = "ollama", model: str = None):
        self.provider = provider
        self.model = model
        self.history: list[ChatMessage] = []
    
    def chat(self, message: str, context: Optional[str] = None) -> ChatMessage:
        """Send a message and get a response."""
        self.history.append(ChatMessage(role="user", content=message))
        
        try:
            from streamlitforge.llm import generate_code, LLMConfig
            
            config = LLMConfig(provider=self.provider, model=self.model, temperature=0.7)
            conversation = self._build_conversation()
            response = generate_code(prompt=message, config=config, context=conversation)
            code = self._extract_code(response)
            reply = ChatMessage(role="assistant", content=response, code=code)
        except Exception as e:
            reply = self._fallback_response(message, str(e))
        
        self.history.append(reply)
        return reply
    
    def _build_conversation(self) -> str:
        if not self.history:
            return ""
        lines = [f"{msg.role.upper()}: {msg.content[:500]}" for msg in self.history[-10:]]
        return "\n".join(lines)
    
    def _extract_code(self, response: str) -> Optional[str]:
        import re
        pattern = r"```python\s*(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        return "\n\n".join(matches) if matches else None
    
    def _fallback_response(self, message: str, error: str) -> ChatMessage:
        # Try to find a similar pattern
        pattern_code = st.session_state.pattern_learner.find_pattern(message)
        if pattern_code:
            return ChatMessage(
                role="assistant",
                content="I found a similar pattern that might help:",
                code=pattern_code,
            )
        
        return ChatMessage(
            role="assistant",
            content=f"I'm currently unable to connect to an LLM provider (error: {error}).\n\nHere's a basic template to get started:",
            code="""import streamlit as st

st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
)

st.title("My Streamlit App")

with st.sidebar:
    st.header("Settings")
    option = st.selectbox("Choose an option", ["A", "B", "C"])

st.write(f"You selected: {option}")""",
        )
    
    def clear_history(self):
        self.history = []


def render():
    """Render the AI Builder page."""
    
    st.title("🤖 AI Builder")
    
    # Check for project
    if not st.session_state.current_project:
        st.warning("Please select or create a project first.")
        if st.button("Go to Projects"):
            st.session_state.active_tab = "📁 Projects"
            st.rerun()
        return
    
    project = st.session_state.current_project
    st.caption(f"Project: **{project.get('name', 'Untitled')}** | {project.get('path', '')}")
    
    # Initialize builder agent
    if st.session_state.builder_agent is None:
        provider = st.session_state.get("selected_provider", "ollama")
        model = st.session_state.get("selected_model", "llama3")
        st.session_state.builder_agent = BuilderAgent(provider=provider, model=model)
    
    agent = st.session_state.builder_agent
    
    # Mode selection with persona integration
    st.subheader("Builder Mode")
    
    mode_col1, mode_col2, mode_col3 = st.columns(3)
    
    current_mode = st.session_state.get("builder_mode", "chat")
    
    with mode_col1:
        if st.button(
            "💬 Chat Mode",
            type="primary" if current_mode == "chat" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "chat"
            st.rerun()
    
    with mode_col2:
        if st.button(
            "🔧 Build Mode",
            type="primary" if current_mode == "build" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "build"
            st.rerun()
    
    with mode_col3:
        if st.button(
            "🎓 Expert Mode",
            type="primary" if current_mode == "expert" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "expert"
            st.rerun()
    
    # Mode description
    mode_descriptions = {
        "chat": "💬 **Chat Mode**: Ask questions, get help, and learn about Streamlit.",
        "build": "🔧 **Build Mode**: Generate code for Streamlit components and apps.",
        "expert": "🎓 **Expert Mode**: Get senior developer guidance with architectural advice.",
    }
    st.info(mode_descriptions.get(current_mode, ""))
    
    # Wire persona for expert mode
    if current_mode == "expert":
        from streamlitforge.persona import SeniorDeveloperPersona
        if "persona" not in st.session_state:
            st.session_state.persona = SeniorDeveloperPersona()
        
        # Show persona domain selector
        domain = st.selectbox(
            "Focus Domain",
            ["architecture", "performance", "security", "deployment", "patterns"],
            key="persona_domain",
        )
    
    st.divider()
    
    # Model and provider info
    with st.sidebar:
        st.subheader("🤖 AI Settings")
        
        provider = st.selectbox(
            "Provider",
            ["ollama", "openai", "anthropic", "groq"],
            index=["ollama", "openai", "anthropic", "groq"].index(
                st.session_state.get("selected_provider", "ollama")
            ),
        )
        st.session_state.selected_provider = provider
        
        models = get_models_for_provider(provider)
        model = st.selectbox("Model", models)
        st.session_state.selected_model = model
        
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        
        st.caption(f"Mode: **{current_mode.title()}**")
        st.caption(f"Provider: **{provider}**")
        st.caption(f"Model: **{model}**")
    
    # Two-column layout: Chat on left, Code preview on right
    col_chat, col_code = st.columns([1, 1])
    
    with col_chat:
        st.subheader("💬 Chat with AI")
        
        # Chat history container
        chat_container = st.container(height=400)
        
        with chat_container:
            # Display chat history
            for msg in agent.history:
                with st.chat_message(msg.role):
                    st.markdown(msg.content[:2000])  # Limit display
                    
                    if msg.code:
                        with st.expander("View Generated Code"):
                            st.code(msg.code, language="python")
        
        # Chat input
        if prompt := st.chat_input("Describe what you want to build..."):
            # Add user message
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # Get AI response with status indicator
            with chat_container:
                with st.chat_message("assistant"):
                    with st.status("Thinking...", expanded=True) as status:
                        st.write("Analyzing your request...")
                        
                        # Build context from current project and mode
                        context = f"Project: {project.get('name')}\nPath: {project.get('path')}\nMode: {current_mode}"
                        
                        # Add persona context for expert mode
                        if current_mode == "expert" and "persona" in st.session_state:
                            domain = st.session_state.get("persona_domain", "architecture")
                            persona_prompt = st.session_state.persona.get_system_prompt(domain)
                            context += f"\n\nPersona Context:\n{persona_prompt}"
                        
                        st.write("Generating Streamlit code...")
                        
                        # Use streaming if available
                        use_streaming = st.session_state.get("use_streaming", True)
                        if use_streaming:
                            response_text = st.write_stream(generate_streaming_response(prompt, context, current_mode))
                        else:
                            response = agent.chat(prompt, context=context)
                            response_text = response.content
                            st.markdown(response_text)
                        
                        status.update(label="Complete!", state="complete")
                        
                        # Extract code from response
                        code = extract_code_from_response(response_text)
                        if code:
                            st.session_state.generated_code = code
                            with st.expander("View Generated Code"):
                                st.code(code, language="python")
    
    with col_code:
        st.subheader("📝 Code Preview")
        
        # Code editor area
        code = st.session_state.get("generated_code", get_current_app_code(project))
        
        edited_code = st.text_area(
            "app.py",
            value=code,
            height=500,
            label_visibility="collapsed",
        )
        
        st.session_state.generated_code = edited_code
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save to Project", type="primary", use_container_width=True):
                save_code_to_project(project, edited_code)
                st.success("Saved!")
        
        with col2:
            if st.button("▶️ Run App", use_container_width=True):
                run_project(project)
                st.success("App starting...")
        
        with col3:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.generated_code = get_current_app_code(project)
                st.rerun()
        
        # File browser
        st.divider()
        st.subheader("📁 Project Files")
        
        project_path = Path(project.get("path", ""))
        if project_path.exists():
            src_path = project_path / "src"
            if src_path.exists():
                for file in src_path.glob("*.py"):
                    with st.expander(f"📄 {file.name}"):
                        if st.button(f"Load", key=f"load_{file}"):
                            st.session_state.generated_code = file.read_text()
                            st.rerun()


def get_models_for_provider(provider: str) -> list:
    """Get available models for a provider."""
    models = {
        "ollama": ["llama3", "llama3:70b", "codellama:7b", "mistral", "deepseek-coder"],
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        "groq": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b"],
    }
    return models.get(provider, ["default"])


def generate_streaming_response(prompt: str, context: str, mode: str):
    """Generate a streaming response from the LLM."""
    from streamlitforge.llm.router import EnhancedLLMRouter
    from streamlitforge.llm.base import Message, MessageRole
    
    # Get configured router
    router = st.session_state.get("llm_router")
    if not router:
        yield "Please configure an LLM provider in Settings."
        return
    
    provider_name = st.session_state.get("selected_provider", "ollama")
    model = st.session_state.get("selected_model", "llama3")
    provider = router.providers.get(provider_name)
    
    if not provider:
        yield f"Provider {provider_name} not configured."
        return
    
    # Build system prompt based on mode
    if mode == "expert":
        from streamlitforge.persona import SENIOR_DEVELOPER_PROMPT
        system_prompt = SENIOR_DEVELOPER_PROMPT
    elif mode == "build":
        system_prompt = """You are StreamlitForge Builder, an expert at generating
clean, idiomatic Streamlit code. Generate only the code needed, with brief
explanations. Follow Streamlit best practices."""
    else:
        system_prompt = """You are StreamlitForge Assistant, helping users learn
and use Streamlit effectively. Provide clear explanations with code examples
when appropriate."""
    
    messages = [
        Message(MessageRole.SYSTEM, system_prompt),
        Message(MessageRole.USER, f"Context: {context}\n\n{prompt}"),
    ]
    
    try:
        for chunk in provider.generate_stream(messages, model=model):
            yield chunk
    except Exception as e:
        yield f"\n\n[Error: {e}]"


def extract_code_from_response(response: str) -> str:
    """Extract Python code blocks from response."""
    import re
    pattern = r"```python\s*(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    return "\n\n".join(matches) if matches else ""


def get_current_app_code(project: dict) -> str:
    """Get the current app.py content from the project."""
    project_path = Path(project.get("path", ""))
    app_file = project_path / "src" / "app.py"
    
    if app_file.exists():
        return app_file.read_text()
    
    return """import streamlit as st

st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
)

st.title("My Streamlit App")

st.write("Hello, StreamlitForge!")
"""


def save_code_to_project(project: dict, code: str):
    """Save code to the project's app.py file."""
    project_path = Path(project.get("path", ""))
    app_file = project_path / "src" / "app.py"
    
    app_file.parent.mkdir(parents=True, exist_ok=True)
    app_file.write_text(code)


def run_project(project: dict):
    """Run the Streamlit project."""
    import subprocess
    
    project_path = Path(project.get("path", ""))
    port = project.get("port", 8501)
    app_file = project_path / "src" / "app.py"
    
    subprocess.Popen(
        ["streamlit", "run", str(app_file), "--server.port", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
