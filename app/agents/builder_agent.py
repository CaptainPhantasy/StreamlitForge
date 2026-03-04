"""Builder Agent - AI-powered Streamlit code generator."""

from dataclasses import dataclass, field
from typing import Optional
import streamlit as st


@dataclass
class ChatMessage:
    """A chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    code: Optional[str] = None


class BuilderAgent:
    """AI agent for building Streamlit applications."""
    
    SYSTEM_PROMPT = """You are an expert Streamlit developer assistant. You help users build Streamlit applications by:

1. Understanding their requirements
2. Generating clean, well-structured Streamlit code
3. Following best practices for Streamlit development
4. Using appropriate Streamlit components (st.dataframe, st.chart, st.sidebar, etc.)
5. Organizing code with proper page structure and layout

When generating code:
- Always import streamlit as st
- Use st.set_page_config() at the top if needed
- Follow PEP 8 style guidelines
- Add helpful comments for complex logic
- Use st.columns() for layouts
- Leverage st.sidebar for settings/controls
- Use st.session_state for state management

Respond with clear explanations and include code in ```python blocks."""
    
    def __init__(self, provider: str = "ollama", model: str = None):
        self.provider = provider
        self.model = model
        self.history: list[ChatMessage] = []
    
    def chat(self, message: str, context: Optional[str] = None) -> ChatMessage:
        """Send a message and get a response."""
        
        # Build the full prompt with context
        full_prompt = message
        if context:
            full_prompt = f"Context: {context}\n\nUser request: {message}"
        
        # Add to history
        self.history.append(ChatMessage(role="user", content=message))
        
        try:
            # Try to use LLM
            from streamlitforge.llm import generate_code, LLMConfig
            
            config = LLMConfig(
                provider=self.provider,
                model=self.model,
                temperature=0.7,
            )
            
            # Build conversation context
            conversation = self._build_conversation()
            
            response = generate_code(
                prompt=full_prompt,
                config=config,
                context=conversation,
            )
            
            # Extract code if present
            code = self._extract_code(response)
            
            reply = ChatMessage(
                role="assistant",
                content=response,
                code=code,
            )
            
        except Exception as e:
            # Fallback to pattern-based generation
            reply = self._fallback_response(message, str(e))
        
        self.history.append(reply)
        return reply
    
    def _build_conversation(self) -> str:
        """Build conversation context from history."""
        if not self.history:
            return ""
        
        lines = []
        for msg in self.history[-10:]:  # Last 10 messages
            lines.append(f"{msg.role.upper()}: {msg.content[:500]}")
        
        return "\n".join(lines)
    
    def _extract_code(self, response: str) -> Optional[str]:
        """Extract Python code blocks from response."""
        import re
        
        pattern = r"```python\s*(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL)
        
        if matches:
            return "\n\n".join(matches)
        return None
    
    def _fallback_response(self, message: str, error: str) -> ChatMessage:
        """Generate fallback response when LLM is unavailable."""
        
        # Try to use pattern library
        pattern_learner = st.session_state.get("pattern_learner")
        
        if pattern_learner:
            # Use find_matching_patterns for better results
            matches = pattern_learner.find_matching_patterns(message, limit=3)
            
            if matches:
                if len(matches) == 1:
                    pattern = matches[0]
                    return ChatMessage(
                        role="assistant",
                        content=f"I found a pattern that might help: **{pattern.get('name', 'pattern')}**",
                        code=pattern.get("template", ""),
                    )
                else:
                    # Multiple matches - combine them
                    combined_code = self._combine_patterns(matches)
                    pattern_names = ", ".join([m.get("name", "") for m in matches])
                    return ChatMessage(
                        role="assistant",
                        content=f"I found {len(matches)} matching patterns ({pattern_names}). Here's a combined template:",
                        code=combined_code,
                    )
        
        # Generic fallback
        return ChatMessage(
            role="assistant",
            content=f"""I'm currently unable to connect to an LLM provider (error: {error}).

Here's a basic Streamlit template to get started:

```python
import streamlit as st

st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",
)

st.title("My Streamlit App")

with st.sidebar:
    st.header("Settings")
    option = st.selectbox("Choose an option", ["A", "B", "C"])

st.write(f"You selected: {option}")
```

To enable AI assistance, configure an LLM provider in Settings.""",
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
    
    def _combine_patterns(self, patterns: list) -> str:
        """Combine multiple patterns into a cohesive application."""
        imports = set(["import streamlit as st"])
        code_blocks = []
        
        for pattern in patterns:
            template = pattern.get("template", "")
            # Extract imports
            for line in template.split("\n"):
                if line.startswith("import ") or line.startswith("from "):
                    imports.add(line)
            
            # Get the main code (skip imports)
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
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []
    
    def get_code_suggestions(self, partial_code: str) -> list[str]:
        """Get code completions/suggestions."""
        # This would use the LLM for code completion
        # For now, return empty
        return []
