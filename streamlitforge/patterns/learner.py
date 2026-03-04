"""Pattern Library with PatternLearner — offline code generation core."""

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class PatternLearner:
    """Learns patterns from successful code generations for offline use."""

    def __init__(self, library_path: str = None, min_examples: int = 3):
        self.library_path = Path(library_path or Path.home() / ".streamlitforge" / "patterns")
        self.min_examples = min_examples
        self.library_path.mkdir(parents=True, exist_ok=True)

    def record_success(
        self,
        prompt: str,
        generated_code: str,
        user_modifications: Optional[str] = None,
    ):
        existing = self._find_similar_pattern(prompt)
        if existing:
            existing["examples"].append({
                "input": prompt,
                "output": generated_code,
                "modified_output": user_modifications,
            })
            existing["usage_count"] = existing.get("usage_count", 0) + 1
            existing["last_used"] = datetime.now(timezone.utc).isoformat()
            self._save_pattern(existing)
        else:
            pattern = self._extract_pattern(generated_code, user_modifications)
            self._create_pattern(prompt, pattern, generated_code)

    def _extract_pattern(self, code: str, modifications: Optional[str] = None) -> Dict[str, Any]:
        final_code = modifications or code
        triggers = self._extract_triggers(final_code)
        variables = self._extract_variables(final_code)
        template = self._templatize(final_code)
        return {
            "triggers": triggers,
            "template": template,
            "variables": variables,
        }

    def _extract_triggers(self, code: str) -> List[str]:
        triggers = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id == "st":
                        triggers.add(node.attr)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == "st":
                        triggers.add(node.func.attr)
        except SyntaxError:
            pass
        st_pattern = re.compile(r"st\.(\w+)")
        for match in st_pattern.finditer(code):
            triggers.add(match.group(1))
        return sorted(triggers)

    def _extract_variables(self, code: str) -> Dict[str, Dict[str, Any]]:
        variables: Dict[str, Dict[str, Any]] = {}
        string_literals = re.findall(r'"([^"]{3,})"', code) + re.findall(r"'([^']{3,})'", code)
        for i, lit in enumerate(string_literals[:5]):
            variables[f"string_{i}"] = {"type": "string", "default": lit}
        return variables

    def _templatize(self, code: str) -> str:
        return code

    def _find_similar_pattern(self, prompt: str) -> Optional[Dict[str, Any]]:
        prompt_lower = prompt.lower()
        prompt_words = set(prompt_lower.split())
        best_match = None
        best_score = 0.0
        for filepath in self.library_path.glob("pattern_*.json"):
            try:
                pattern = json.loads(filepath.read_text())
                triggers = set(t.lower() for t in pattern.get("triggers", []))
                intersection = prompt_words & triggers
                if triggers:
                    score = len(intersection) / len(triggers)
                    if score > best_score:
                        best_score = score
                        best_match = pattern
            except (json.JSONDecodeError, OSError):
                continue
        return best_match if best_score > 0.3 else None

    def _create_pattern(self, prompt: str, pattern_data: Dict, generated_code: str):
        pattern_id = re.sub(r"\W+", "_", prompt.lower()[:50]).strip("_")
        pattern = {
            "pattern_id": pattern_id,
            "name": prompt[:100],
            "triggers": pattern_data.get("triggers", []),
            "template": pattern_data.get("template", generated_code),
            "variables": pattern_data.get("variables", {}),
            "examples": [{"input": prompt, "output": generated_code}],
            "usage_count": 1,
            "last_used": datetime.now(timezone.utc).isoformat(),
        }
        self._save_pattern(pattern)

    def _save_pattern(self, pattern: Dict):
        pattern_id = pattern.get("pattern_id", "unknown")
        filepath = self.library_path / f"pattern_{pattern_id}.json"
        filepath.write_text(json.dumps(pattern, indent=2))

    def find_pattern(self, query: str) -> Optional[str]:
        match = self._find_similar_pattern(query)
        if match:
            return match.get("template", "")
        return None

    def list_patterns(self) -> List[Dict[str, Any]]:
        patterns = []
        for filepath in sorted(self.library_path.glob("pattern_*.json")):
            try:
                p = json.loads(filepath.read_text())
                patterns.append({
                    "pattern_id": p.get("pattern_id"),
                    "name": p.get("name"),
                    "triggers": p.get("triggers", []),
                    "usage_count": p.get("usage_count", 0),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return patterns

    def get_pattern_count(self) -> int:
        return len(list(self.library_path.glob("pattern_*.json")))
