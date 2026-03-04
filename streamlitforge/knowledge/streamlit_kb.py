"""Streamlit Knowledge Base with web grounding and offline fallback."""

import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class StreamlitKnowledgeBase:
    """Maintains up-to-date Streamlit knowledge via web grounding with offline fallback."""

    def __init__(self, cache_path: str = None, cache_expiry_hours: int = 24):
        self.cache_path = Path(cache_path or Path.home() / ".streamlitforge" / "knowledge")
        self.cache_expiry = cache_expiry_hours
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def _is_cache_valid(self, cache_file: Path, hours: int = None) -> bool:
        if not cache_file.exists():
            return False
        try:
            data = json.loads(cache_file.read_text())
            fetched_at = data.get("fetched_at", "")
            if not fetched_at:
                return False
            fetched_time = datetime.fromisoformat(fetched_at)
            if fetched_time.tzinfo is None:
                fetched_time = fetched_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            diff_hours = (now - fetched_time).total_seconds() / 3600
            return diff_hours < (hours or self.cache_expiry)
        except (json.JSONDecodeError, ValueError, KeyError):
            return False

    def get_latest_features(self) -> Dict[str, Any]:
        cache_file = self.cache_path / "features.json"
        if self._is_cache_valid(cache_file):
            try:
                return json.loads(cache_file.read_text())["data"]
            except (json.JSONDecodeError, KeyError):
                pass

        try:
            features = self._fetch_features_from_web()
            cache_file.write_text(json.dumps({
                "data": features,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }))
            return features
        except Exception:
            if cache_file.exists():
                try:
                    return json.loads(cache_file.read_text())["data"]
                except (json.JSONDecodeError, KeyError):
                    pass
            return self._get_builtin_features()

    def _fetch_features_from_web(self) -> Dict[str, Any]:
        try:
            resp = requests.get("https://pypi.org/pypi/streamlit/json", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            version = data["info"]["version"]
            features = self._get_builtin_features()
            features["version"] = version
            return features
        except Exception:
            return self._get_builtin_features()

    def search_examples(self, query: str, limit: int = 5) -> List[Dict]:
        results = self._search_local_examples(query)
        return results[:limit]

    def _search_local_examples(self, query: str) -> List[Dict]:
        features = self._get_builtin_features()
        results = []
        query_lower = query.lower()
        for category, items in features.get("features", {}).items():
            for item in items:
                if query_lower in item.lower() or query_lower in category.lower():
                    results.append({
                        "title": item,
                        "category": category,
                        "type": "api",
                    })
        return results

    def get_deprecations(self) -> List[Dict]:
        features = self._get_builtin_features()
        return features.get("deprecations", [])

    def get_best_practices(self) -> List[str]:
        features = self._get_builtin_features()
        return features.get("best_practices", [])

    def get_current_version(self) -> str:
        try:
            resp = requests.get("https://pypi.org/pypi/streamlit/json", timeout=10)
            resp.raise_for_status()
            return resp.json()["info"]["version"]
        except Exception:
            cache_file = self.cache_path / "features.json"
            if cache_file.exists():
                try:
                    return json.loads(cache_file.read_text())["data"]["version"]
                except (json.JSONDecodeError, KeyError):
                    pass
            return "1.41.0"

    def _get_builtin_features(self) -> Dict[str, Any]:
        return {
            "version": "1.41.0",
            "features": {
                "chat": ["st.chat_message", "st.chat_input"],
                "data": ["st.dataframe", "st.data_editor", "st.table"],
                "charts": [
                    "st.line_chart", "st.bar_chart", "st.area_chart",
                    "st.scatter_chart", "st.map",
                ],
                "input": [
                    "st.text_input", "st.text_area", "st.number_input",
                    "st.slider", "st.selectbox", "st.multiselect",
                    "st.checkbox", "st.radio", "st.date_input",
                    "st.time_input", "st.file_uploader", "st.color_picker",
                    "st.camera_input",
                ],
                "layout": [
                    "st.columns", "st.tabs", "st.expander",
                    "st.sidebar", "st.container", "st.empty",
                ],
                "media": ["st.image", "st.audio", "st.video"],
                "status": [
                    "st.progress", "st.spinner", "st.status",
                    "st.toast", "st.balloons", "st.snow",
                ],
                "navigation": ["st.navigation", "st.Page", "st.switch_page"],
                "cache": ["st.cache_data", "st.cache_resource"],
                "session": ["st.session_state"],
                "theme": ["st.get_option", "st.set_option"],
            },
            "deprecations": [
                {
                    "feature": "use_container_width",
                    "replacement": "width='stretch' or width='content'",
                    "removed_after": "2025-12-31",
                },
                {
                    "feature": "@st.cache",
                    "replacement": "@st.cache_data or @st.cache_resource",
                    "removed_after": "2024-01-01",
                },
            ],
            "best_practices": [
                "Use st.set_page_config() as first command",
                "Use st.session_state for state persistence",
                "Use @st.cache_data for expensive computations",
                "Use st.columns for layouts, avoid nested columns",
                "Use st.toast for non-blocking notifications",
                "Use st.status for long-running operations",
            ],
        }
