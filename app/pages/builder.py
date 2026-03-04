"""AI Builder page - Main interface for building Streamlit apps with AI."""

import streamlit as st
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


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
        self.history: List[ChatMessage] = []
    
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
        """Generate fallback response when LLM is unavailable using pattern library."""
        # Try to find matching patterns
        pattern_learner = st.session_state.get("pattern_learner")
        
        if pattern_learner:
            # Use find_matching_patterns to get multiple results
            matches = pattern_learner.find_matching_patterns(message, limit=3)
            
            if matches:
                # Combine patterns if multiple matches
                if len(matches) == 1:
                    pattern = matches[0]
                    return ChatMessage(
                        role="assistant",
                        content=f"I found a pattern that might help (matched: **{pattern.get('name', 'pattern')}**):",
                        code=pattern.get("template", ""),
                    )
                else:
                    # Combine multiple patterns into a cohesive app
                    combined_code = _combine_patterns(matches)
                    pattern_names = ", ".join([m.get("name", "pattern") for m in matches])
                    return ChatMessage(
                        role="assistant",
                        content=f"I found {len(matches)} matching patterns ({pattern_names}). Here's a combined template:",
                        code=combined_code,
                    )
        
        # Ultimate fallback - basic template
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


def _combine_patterns(patterns: list) -> str:
    """Combine multiple patterns into a cohesive application."""
    imports = set(["import streamlit as st"])
    code_blocks = []
    
    for pattern in patterns:
        template = pattern.get("template", "")
        # Extract imports
        for line in template.split("\n"):
            if line.startswith("import ") or line.startswith("from "):
                imports.add(line)
        
        # Get the main code (skip imports for now)
        code_lines = []
        for line in template.split("\n"):
            if not (line.startswith("import ") or line.startswith("from ")):
                code_lines.append(line)
        
        code_blocks.append("\n".join(code_lines).strip())
    
    # Build combined code
    result = "# Generated Streamlit Application\n\n"
    result += "\n".join(sorted(imports)) + "\n\n"
    result += 'st.set_page_config(page_title="My App", page_icon="🚀", layout="wide")\n\n'
    result += 'st.title("My Streamlit App")\n\n'
    
    for i, block in enumerate(code_blocks):
        if block and not block.startswith("st.set_page_config"):
            result += f"# Section {i+1}\n{block}\n\n"
    
    return result.strip()


# System prompts for different modes
FULL_APP_SYSTEM_PROMPT = """You are StreamlitForge Full App Builder, an expert at creating complete, 
production-ready Streamlit applications from natural language descriptions.

When a user describes an app they want:
1. Create a COMPLETE, runnable Streamlit application
2. Include proper page configuration (st.set_page_config)
3. Use appropriate layouts (sidebar, columns, tabs, etc.)
4. Include all necessary imports
5. Add error handling and input validation
6. Follow Streamlit best practices
7. Use st.session_state for state management
8. Add helpful comments
9. Include sample data or data loading logic
10. Make it look professional with proper titles, headers, and organization

Your response should be the complete Python code that the user can run immediately.
Always wrap code in ```python blocks.

The app should be ready to run without modifications - include realistic sample data, 
proper styling, and all the features the user requested."""


def render():
    """Render the AI Builder page."""
    
    st.title("🤖 AI Builder")
    
    # REMOVED: Project requirement barrier - now allows immediate chat
    # Show project status if one is selected, but don't require it
    project = st.session_state.current_project
    if project:
        st.caption(f"📁 Project: **{project.get('name', 'Untitled')}** | {project.get('path', '')}")
    else:
        st.caption("💡 **Quick Mode**: Chat now, save to a project later. Select a project in the sidebar to enable saving.")
    
    # Initialize builder agent
    if st.session_state.builder_agent is None:
        provider = st.session_state.get("selected_provider", "ollama")
        model = st.session_state.get("selected_model", "llama3")
        st.session_state.builder_agent = BuilderAgent(provider=provider, model=model)
    
    agent = st.session_state.builder_agent
    
    # Mode selection with FOUR modes now
    st.subheader("Builder Mode")
    
    mode_col1, mode_col2, mode_col3, mode_col4 = st.columns(4)
    
    current_mode = st.session_state.get("builder_mode", "full_app")  # Default to full_app
    
    with mode_col1:
        if st.button(
            "💬 Chat",
            type="primary" if current_mode == "chat" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "chat"
            st.rerun()
    
    with mode_col2:
        if st.button(
            "🔧 Build",
            type="primary" if current_mode == "build" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "build"
            st.rerun()
    
    with mode_col3:
        if st.button(
            "🚀 Full App",
            type="primary" if current_mode == "full_app" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "full_app"
            st.rerun()
    
    with mode_col4:
        if st.button(
            "🎓 Expert",
            type="primary" if current_mode == "expert" else "secondary",
            use_container_width=True,
        ):
            st.session_state.builder_mode = "expert"
            st.rerun()
    
    # Mode description
    mode_descriptions = {
        "chat": "💬 **Chat Mode**: Ask questions, get help, and learn about Streamlit.",
        "build": "🔧 **Build Mode**: Generate code snippets and components.",
        "full_app": "🚀 **Full App Mode**: Describe your app and get a complete, working application!",
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
    
    # Show helpful prompts for Full App mode
    if current_mode == "full_app":
        st.subheader("💡 Example Prompts")
        example_prompts = [
            "Build me a dashboard that shows sales metrics with charts and KPIs",
            "Create a data analysis app that lets users upload CSV files and visualize them",
            "Make a to-do list app with the ability to add, edit, and delete tasks",
            "Build a form builder that creates contact forms and saves submissions",
            "Create an image gallery app with upload and filtering capabilities",
        ]
        cols = st.columns(3)
        for i, prompt in enumerate(example_prompts[:3]):
            with cols[i]:
                if st.button(f"📝 {prompt[:30]}...", key=f"example_{i}"):
                    st.session_state.example_prompt = prompt
                    st.rerun()
    
    st.divider()
    
    # Model and provider info
    with st.sidebar:
        st.subheader("🤖 AI Settings")
        
        provider = st.selectbox(
            "Provider",
            ["ollama", "openai", "anthropic", "groq", "openrouter", "opencode"],
            index=["ollama", "openai", "anthropic", "groq", "openrouter", "opencode"].index(
                st.session_state.get("selected_provider", "ollama")
            ) if st.session_state.get("selected_provider") in ["ollama", "openai", "anthropic", "groq", "openrouter", "opencode"] else 0,
        )
        st.session_state.selected_provider = provider
        
        models = get_models_for_provider(provider)
        model = st.selectbox("Model", models)
        st.session_state.selected_model = model
        
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        
        st.caption(f"Mode: **{current_mode.replace('_', ' ').title()}**")
        st.caption(f"Provider: **{provider}**")
        st.caption(f"Model: **{model}**")
        
        # Show pattern library status
        st.divider()
        st.subheader("📚 Pattern Library")
        pattern_learner = st.session_state.get("pattern_learner")
        if pattern_learner:
            builtin_count = pattern_learner.get_builtin_pattern_count()
            total_count = pattern_learner.get_pattern_count()
            st.metric("Built-in Patterns", builtin_count)
            st.metric("Total Patterns", total_count)
        else:
            st.warning("Pattern library not loaded")
    
    # Two-column layout: Chat on left, Code preview on right
    col_chat, col_code = st.columns([1, 1])
    
    with col_chat:
        st.subheader("💬 Chat with AI")
        
        # Voice input note
        st.caption("🎤 **Tip**: Use your browser's voice-to-text feature (usually in the keyboard on mobile, or dictation on desktop) to speak your requests!")
        
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
        
        # Chat input - handle example prompts via session state
        chat_placeholder = st.session_state.pop("example_prompt", "")
        prompt = st.chat_input("Describe what you want to build...")
        
        # If no input but we have an example prompt, use it
        if not prompt and chat_placeholder:
            prompt = chat_placeholder
        
        if prompt:
            # Add user message to history
            agent.history.append(ChatMessage(role="user", content=prompt))
            
            # Add user message to display
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            
            # Get AI response with status indicator
            with chat_container:
                with st.chat_message("assistant"):
                    with st.status("Thinking...", expanded=True) as status:
                        st.write("Analyzing your request...")
                        
                        # Build context from current project and mode
                        if project:
                            context = f"Project: {project.get('name')}\nPath: {project.get('path')}\nMode: {current_mode}"
                        else:
                            context = f"Mode: {current_mode}\nNote: No project selected - generating standalone app."
                        
                        # Add persona context for expert mode
                        if current_mode == "expert" and "persona" in st.session_state:
                            domain = st.session_state.get("persona_domain", "architecture")
                            persona_prompt = st.session_state.persona.get_system_prompt(domain)
                            context += f"\n\nPersona Context:\n{persona_prompt}"
                        
                        st.write("Generating Streamlit code...")
                        
                        # Use streaming if available
                        use_streaming = st.session_state.get("use_streaming", True)
                        try:
                            if use_streaming:
                                response_text = st.write_stream(generate_streaming_response(prompt, context, current_mode))
                            else:
                                response = agent.chat(prompt, context=context)
                                response_text = response.content
                                st.markdown(response_text)
                        except Exception as e:
                            # Fallback to pattern-based response
                            st.write("⚠️ LLM unavailable, using pattern library...")
                            response = agent._fallback_response(prompt, str(e))
                            response_text = response.content
                            st.markdown(response_text)
                        
                        status.update(label="Complete!", state="complete")
                        
                        # Extract code from response
                        code = extract_code_from_response(response_text)
                        if code:
                            st.session_state.generated_code = code
                            with st.expander("View Generated Code", expanded=True):
                                st.code(code, language="python")
                        
                        # Add assistant response to history (if not already added by agent.chat)
                        if use_streaming:
                            agent.history.append(ChatMessage(role="assistant", content=response_text, code=code))
    
    with col_code:
        st.subheader("📝 Code Preview")
        
        # Code editor area
        if project:
            default_code = st.session_state.get("generated_code", get_current_app_code(project))
        else:
            default_code = st.session_state.get("generated_code", get_default_template())
        
        edited_code = st.text_area(
            "app.py",
            value=default_code,
            height=500,
            label_visibility="collapsed",
        )
        
        st.session_state.generated_code = edited_code
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Save button - requires project
            if project:
                if st.button("💾 Save to Project", type="primary", use_container_width=True):
                    save_code_to_project(project, edited_code)
                    st.success("Saved!")
            else:
                st.button("💾 Save to Project", use_container_width=True, disabled=True)
                st.caption("Select a project first")
        
        with col2:
            # Run button - requires project
            if project:
                if st.button("▶️ Run App", use_container_width=True):
                    run_project(project)
                    st.success("App starting...")
            else:
                st.button("▶️ Run App", use_container_width=True, disabled=True)
                st.caption("Select a project first")
        
        with col3:
            # Download code as file (reliable way to "copy")
            st.download_button(
                label="📋 Download Code",
                data=edited_code,
                file_name="app.py",
                mime="text/x-python",
                use_container_width=True,
            )
        
        with col4:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.generated_code = get_default_template()
                st.rerun()
        
        # Quick Run - run code without needing a project
        st.divider()
        st.subheader("🚀 Test Your Code")
        
        if st.button("▶️ Run in Test Environment", type="primary", use_container_width=True):
            # Save to temp file and run
            import tempfile
            import subprocess
            import time
            
            # Create temp directory for the test app
            test_dir = Path(tempfile.gettempdir()) / "streamlitforge_test"
            test_dir.mkdir(exist_ok=True)
            
            # Use timestamp to create unique test app
            timestamp = int(time.time())
            test_file = test_dir / f"test_app_{timestamp}.py"
            
            # Write the code
            test_file.write_text(edited_code)
            
            # Use PortManager to get an available port
            port_manager = st.session_state.port_manager
            test_port = port_manager.get_port(str(test_file))
            
            # Find streamlit executable
            streamlit_path = "/Users/douglastalley/.local/bin/streamlit"
            
            # Run the test app on the assigned port
            try:
                proc = subprocess.Popen(
                    [streamlit_path, "run", str(test_file), "--server.port", str(test_port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                st.success(f"✅ Test app running!")
                st.markdown(f"**[Open Test App on Port {test_port} →](http://localhost:{test_port})**")
                st.caption(f"PID: {proc.pid} | Port: {test_port} | File: `{test_file.name}`")
            except Exception as e:
                st.error(f"Failed to run: {e}")
        
        # Show currently running test apps
        running_ports = st.session_state.port_manager.list_ports()
        if running_ports:
            with st.expander(f"📊 Running Apps ({len(running_ports)})", expanded=False):
                for port_str, entry in running_ports.items():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"**[Port {port_str}](http://localhost:{port_str})**")
                    with col2:
                        st.caption(entry.get("project_name", "Unknown")[:30])
                    with col3:
                        if st.button("❌", key=f"kill_{port_str}"):
                            st.session_state.port_manager.release_port(entry.get("project_path", ""))
                            st.rerun()
        
        st.caption("⚠️ Note: Test apps need required packages (like `requests`, `beautifulsoup4`) installed.")
        
        # File browser (only if project exists)
        if project:
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
        "openrouter": [
            "openai/gpt-4o-mini",
            "openai/gpt-4o",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-pro-1.5",
            "meta-llama/llama-3.1-70b-instruct",
        ],
        "opencode": [
            "claude-sonnet-4-6",
            "claude-opus-4-6",
            "gpt-5-turbo",
            "gemini-3-pro",
            "minimax-m2.5-free",
            "big-pickle",
            "gpt-5-nano",
        ],
    }
    return models.get(provider, ["default"])


def generate_streaming_response(prompt: str, context: str, mode: str):
    """Generate a streaming response from the LLM."""
    from streamlitforge.llm.router import EnhancedLLMRouter
    from streamlitforge.llm.base import Message, MessageRole
    
    # Ensure router is initialized
    router = st.session_state.get("llm_router")
    if not router:
        # Try to initialize router
        try:
            router = _initialize_router()
            st.session_state.llm_router = router
        except Exception as e:
            router = None
    
    if not router or not router.providers:
        # Try to get response from pattern library
        pattern_learner = st.session_state.get("pattern_learner")
        if pattern_learner:
            matches = pattern_learner.find_matching_patterns(prompt, limit=3)
            if matches:
                if len(matches) == 1:
                    pattern = matches[0]
                    yield f"I found a pattern that might help (matched: **{pattern.get('name', 'pattern')}**):\n\n```python\n{pattern.get('template', '')}\n```"
                    return
                else:
                    combined = _combine_patterns(matches)
                    names = ", ".join([m.get("name", "pattern") for m in matches])
                    yield f"I found {len(matches)} matching patterns ({names}). Here's a combined template:\n\n```python\n{combined}\n```"
                    return
        
        yield "⚠️ No LLM provider available. Go to **Settings** to add an API key, or describe what you need and I'll try to find a matching pattern."
        return
    
    provider_name = st.session_state.get("selected_provider", "ollama")
    model = st.session_state.get("selected_model", "llama3")
    provider = router.providers.get(provider_name)
    
    if not provider:
        # Fallback to pattern library if provider not found
        pattern_learner = st.session_state.get("pattern_learner")
        if pattern_learner:
            matches = pattern_learner.find_matching_patterns(prompt, limit=3)
            if matches:
                combined = _combine_patterns(matches)
                yield f"Provider **{provider_name}** not configured. I found a pattern that might help:\n\n```python\n{combined}\n```"
                return
        
        yield f"⚠️ Provider **{provider_name}** not configured. Go to **Settings** to set up the API key."
        return
    
    # Build system prompt based on mode
    if mode == "expert":
        from streamlitforge.persona import SENIOR_DEVELOPER_PROMPT
        system_prompt = SENIOR_DEVELOPER_PROMPT
    elif mode == "full_app":
        system_prompt = FULL_APP_SYSTEM_PROMPT
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
    except IndexError as e:
        # Specific handling for index errors
        yield f"\n\n⚠️ Response interrupted. The AI response may be incomplete."
    except Exception as e:
        yield f"\n\n⚠️ Error: {str(e)}"


def _initialize_router():
    """Initialize the LLM router with available providers."""
    from streamlitforge.llm.router import EnhancedLLMRouter
    from streamlitforge.core.api_keys import APIKeyManager
    
    km = APIKeyManager()
    providers = {}
    
    # Always try to add Ollama
    try:
        from streamlitforge.llm.providers.ollama import OllamaProvider
        providers["ollama"] = OllamaProvider()
    except Exception:
        pass
    
    # Add other providers if configured
    provider_configs = [
        ("openai", "streamlitforge.llm.providers.openai", "OpenAIProvider"),
        ("anthropic", "streamlitforge.llm.providers.anthropic", "AnthropicProvider"),
        ("groq", "streamlitforge.llm.providers.groq", "GroqProvider"),
        ("openrouter", "streamlitforge.llm.providers.openrouter", "OpenRouterProvider"),
        ("opencode", "streamlitforge.llm.providers.opencode", "OpenCodeZenProvider"),
    ]
    
    for key_name, module_path, class_name in provider_configs:
        if km.get(key_name):
            try:
                import importlib
                module = importlib.import_module(module_path)
                provider_class = getattr(module, class_name)
                providers[key_name] = provider_class(api_key=km.get(key_name))
            except Exception:
                pass
    
    return EnhancedLLMRouter(providers=providers)


def extract_code_from_response(response: str) -> str:
    """Extract Python code blocks from response."""
    import re
    pattern = r"```python\s*(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL)
    return "\n\n".join(matches) if matches else ""


def get_default_template() -> str:
    """Get the default template for code preview."""
    return """import streamlit as st

st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
)

st.title("My Streamlit App")

st.write("Hello, StreamlitForge!")
st.info("Describe what you want to build in the chat, and I'll generate the code for you!")
"""


def get_current_app_code(project: dict) -> str:
    """Get the current app.py content from the project."""
    project_path = Path(project.get("path", ""))
    app_file = project_path / "src" / "app.py"
    
    if app_file.exists():
        return app_file.read_text()
    
    return get_default_template()


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
