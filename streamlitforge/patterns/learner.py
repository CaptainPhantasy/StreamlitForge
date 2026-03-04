"""Pattern Library with PatternLearner — offline code generation core."""

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import importlib.resources


# Built-in pattern files to load on initialization
BUILTIN_PATTERN_FILES = [
    "streamlit_components.json",
    "charts.json",
    "forms.json",
    "layouts.json",
    "data_handlers.json",
]


class PatternLearner:
    """Learns patterns from successful code generations for offline use.
    
    On initialization, loads built-in patterns from streamlitforge/patterns/*.json
    and combines them with user-learned patterns from ~/.streamlitforge/patterns/
    """

    def __init__(self, library_path: str = None, min_examples: int = 3):
        self.library_path = Path(library_path or Path.home() / ".streamlitforge" / "patterns")
        self.min_examples = min_examples
        self.library_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory pattern cache loaded from built-in JSON files
        self._builtin_patterns: Dict[str, Dict[str, Any]] = {}
        self._load_builtin_patterns()
    
    def _load_builtin_patterns(self):
        """Load built-in patterns from streamlitforge/patterns/*.json"""
        patterns_dir = Path(__file__).parent
        
        for pattern_file in BUILTIN_PATTERN_FILES:
            filepath = patterns_dir / pattern_file
            if filepath.exists():
                try:
                    data = json.loads(filepath.read_text())
                    for pattern_id, pattern_data in data.items():
                        # Store with full metadata
                        self._builtin_patterns[pattern_id] = {
                            "pattern_id": pattern_id,
                            "source": "builtin",
                            "name": pattern_data.get("name", pattern_id.replace("_", " ").title()),
                            "triggers": pattern_data.get("triggers", []),
                            "template": pattern_data.get("template", ""),
                            "variables": pattern_data.get("variables", {}),
                            "examples": pattern_data.get("examples", []),
                            "usage_count": 0,
                        }
                except (json.JSONDecodeError, OSError) as e:
                    print(f"Warning: Could not load pattern file {filepath}: {e}")
    
    def get_builtin_pattern_count(self) -> int:
        """Return number of built-in patterns loaded."""
        return len(self._builtin_patterns)

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
        """Find a matching pattern for the query.
        
        Searches built-in patterns first, then user-learned patterns.
        Returns the template code if found, None otherwise.
        """
        # First search built-in patterns
        builtin_match = self._search_patterns(query, self._builtin_patterns)
        if builtin_match:
            return builtin_match.get("template", "")
        
        # Then search user-learned patterns
        match = self._find_similar_pattern(query)
        if match:
            return match.get("template", "")
        
        return None
    
    def find_matching_patterns(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find all matching patterns for a query, returning multiple results.
        
        Useful for showing options or combining patterns.
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Search built-in patterns
        for pattern_id, pattern in self._builtin_patterns.items():
            triggers = set(t.lower() for t in pattern.get("triggers", []))
            intersection = query_words & triggers
            if intersection:
                score = len(intersection) / max(len(triggers), 1)
                results.append({**pattern, "score": score, "source": "builtin"})
        
        # Search user patterns
        for filepath in self.library_path.glob("pattern_*.json"):
            try:
                pattern = json.loads(filepath.read_text())
                triggers = set(t.lower() for t in pattern.get("triggers", []))
                intersection = query_words & triggers
                if intersection:
                    score = len(intersection) / max(len(triggers), 1)
                    results.append({**pattern, "score": score, "source": "user"})
            except (json.JSONDecodeError, OSError):
                continue
        
        # Sort by score and return top results
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:limit]
    
    def _search_patterns(self, query: str, patterns: Dict[str, Dict]) -> Optional[Dict]:
        """Search a dictionary of patterns for a query match."""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        best_match = None
        best_score = 0.0
        
        for pattern_id, pattern in patterns.items():
            triggers = set(t.lower() for t in pattern.get("triggers", []))
            
            # Check for trigger word matches
            intersection = query_words & triggers
            if triggers:
                score = len(intersection) / len(triggers)
                if score > best_score:
                    best_score = score
                    best_match = pattern
            
            # Also check if pattern name appears in query
            name = pattern.get("name", "").lower()
            if name and name in query_lower:
                if 0.5 > best_score:  # Name match is good but trigger match is better
                    best_score = 0.5
                    best_match = pattern
        
        return best_match if best_score > 0.2 else None

    def list_patterns(self) -> List[Dict[str, Any]]:
        """List all patterns - both built-in and user-learned."""
        patterns = []
        
        # Add built-in patterns
        for pattern_id, pattern in self._builtin_patterns.items():
            patterns.append({
                "pattern_id": pattern_id,
                "name": pattern.get("name", pattern_id),
                "triggers": pattern.get("triggers", []),
                "usage_count": pattern.get("usage_count", 0),
                "source": "builtin",
            })
        
        # Add user patterns
        for filepath in sorted(self.library_path.glob("pattern_*.json")):
            try:
                p = json.loads(filepath.read_text())
                patterns.append({
                    "pattern_id": p.get("pattern_id"),
                    "name": p.get("name"),
                    "triggers": p.get("triggers", []),
                    "usage_count": p.get("usage_count", 0),
                    "source": "user",
                })
            except (json.JSONDecodeError, OSError):
                continue
        return patterns

    def get_pattern_count(self) -> int:
        """Total pattern count including built-in patterns."""
        user_count = len(list(self.library_path.glob("pattern_*.json")))
        return user_count + len(self._builtin_patterns)
