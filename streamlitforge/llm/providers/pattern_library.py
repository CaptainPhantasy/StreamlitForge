"""Pattern Library — offline fallback provider."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import LLMProvider, LLMResponse, Message


class PatternLibraryProvider(LLMProvider):
    PROVIDER_NAME = "pattern_library"

    PATTERN_FILES = [
        "streamlit_components.json",
        "data_handlers.json",
        "charts.json",
        "forms.json",
        "authentication.json",
        "layouts.json",
    ]

    def __init__(self, library_path: str = None, **kwargs):
        self.library_path = Path(library_path or Path.home() / ".streamlitforge" / "patterns")
        self.patterns: Dict[str, Any] = self._load_patterns()

    def _load_patterns(self) -> Dict[str, Any]:
        patterns: Dict[str, Any] = {}
        for filename in self.PATTERN_FILES:
            filepath = self.library_path / filename
            if filepath.exists():
                try:
                    with open(filepath) as f:
                        patterns.update(json.load(f))
                except (json.JSONDecodeError, OSError):
                    continue
        return patterns

    def is_available(self) -> bool:
        return True

    def generate(self, messages: List[Message], **kwargs) -> LLMResponse:
        user_message = messages[-1].content if messages else ""
        best_match = None
        best_score = 0.0

        for pattern_key, pattern_data in self.patterns.items():
            score = self._calculate_similarity(user_message, pattern_key)
            if score > best_score:
                best_score = score
                best_match = pattern_data

        if best_match and best_score > 0.3 and isinstance(best_match, dict):
            content = self._substitute(best_match.get("template", ""), user_message)
        else:
            content = self._get_generic_response(user_message)

        return LLMResponse(
            content=content,
            provider=self.PROVIDER_NAME,
            model="offline",
            cached=True,
            cost_estimate=0.0,
        )

    def _calculate_similarity(self, query: str, pattern_key: str) -> float:
        query_words = set(query.lower().split())
        pattern_words = set(pattern_key.lower().replace("_", " ").split())
        union = query_words | pattern_words
        if not union:
            return 0.0
        return len(query_words & pattern_words) / len(union)

    def _substitute(self, template: str, query: str) -> str:
        words = re.findall(r"\b\w+\b", query.lower())
        component_name = "_".join(words[:3]) if words else "component"
        return template.replace("{{ component_name }}", component_name)

    def _get_generic_response(self, query: str) -> str:
        return '''import streamlit as st

st.set_page_config(page_title="App", page_icon="🎯", layout="wide")

st.title("Welcome")
st.write("This is a generated template. Customize as needed.")
'''

    def get_model_info(self) -> Dict[str, Any]:
        info = super().get_model_info()
        info["pattern_count"] = len(self.patterns)
        info["library_path"] = str(self.library_path)
        return info

    def match(self, query: str) -> Optional[str]:
        from ..base import MessageRole, Message as Msg
        resp = self.generate([Msg(role=MessageRole.USER, content=query)])
        return resp.content
