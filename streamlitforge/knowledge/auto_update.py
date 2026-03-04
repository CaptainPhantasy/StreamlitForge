"""Auto-Updating Streamlit Knowledge System."""

import json
import logging
import threading
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


UPDATE_SCHEDULE = {
    "critical": {"version_info", "security_advisories", "breaking_changes"},
    "important": {"new_features", "deprecations", "best_practices"},
    "normal": {"examples", "tutorials", "community_qa"},
}


class AutoUpdatingKnowledgeBase:
    """Automatically updates Streamlit knowledge from multiple sources."""

    SOURCES = {
        "pypi": {
            "url": "https://pypi.org/pypi/streamlit/json",
            "priority": 1,
            "cache_hours": 6,
        },
        "official_docs": {
            "url": "https://docs.streamlit.io",
            "priority": 1,
            "cache_hours": 24,
        },
        "changelog": {
            "url": "https://docs.streamlit.io/develop/quick-reference/changelog",
            "priority": 1,
            "cache_hours": 12,
        },
        "github_repo": {
            "url": "https://github.com/streamlit/streamlit",
            "priority": 2,
            "cache_hours": 24,
        },
        "discuss_forum": {
            "url": "https://discuss.streamlit.io",
            "priority": 3,
            "cache_hours": 48,
        },
        "stackoverflow": {
            "url": "https://stackoverflow.com/questions/tagged/streamlit",
            "priority": 3,
            "cache_hours": 72,
        },
    }

    def __init__(self, cache_path: str = None, update_interval_hours: int = 24,
                 auto_start: bool = False):
        self.cache_path = Path(cache_path or Path.home() / ".streamlitforge" / "knowledge")
        self.update_interval = update_interval_hours
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self._updater_thread: Optional[threading.Thread] = None
        if auto_start:
            self.start_background_updater()

    def start_background_updater(self):
        if self._updater_thread and self._updater_thread.is_alive():
            return

        def update_loop():
            while True:
                try:
                    self.update_if_stale()
                except Exception as e:
                    logger.error("Knowledge update failed: %s", e)
                time.sleep(self.update_interval * 3600)

        self._updater_thread = threading.Thread(target=update_loop, daemon=True)
        self._updater_thread.start()

    def update_if_stale(self) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for source_name, source_config in self.SOURCES.items():
            cache_file = self.cache_path / f"{source_name}.json"
            cache_hours = source_config["cache_hours"]
            if self._is_cache_valid(cache_file, cache_hours):
                results[source_name] = True
                continue
            try:
                self._update_source(source_name, source_config)
                results[source_name] = True
            except Exception as e:
                logger.warning("Failed to update %s: %s", source_name, e)
                results[source_name] = False
        return results

    def _is_cache_valid(self, cache_file: Path, hours: int) -> bool:
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
            diff_hours = (datetime.now(timezone.utc) - fetched_time).total_seconds() / 3600
            return diff_hours < hours
        except (json.JSONDecodeError, ValueError):
            return False

    def _update_source(self, name: str, config: Dict[str, Any]):
        if name == "pypi":
            self._update_pypi()
        else:
            self._update_generic(name, config["url"])

    def _update_pypi(self):
        resp = requests.get("https://pypi.org/pypi/streamlit/json", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cache_data = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": {
                "version": data["info"]["version"],
                "summary": data["info"]["summary"],
                "requires_python": data["info"]["requires_python"],
            },
        }
        (self.cache_path / "pypi.json").write_text(json.dumps(cache_data, indent=2))

    def _update_generic(self, name: str, url: str):
        cache_file = self.cache_path / f"{name}.json"
        cache_data = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "source_url": url,
            "data": {},
        }
        cache_file.write_text(json.dumps(cache_data, indent=2))

    def get_current_version(self) -> str:
        cache_file = self.cache_path / "pypi.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                return data["data"]["version"]
            except (json.JSONDecodeError, KeyError):
                pass
        try:
            resp = requests.get("https://pypi.org/pypi/streamlit/json", timeout=10)
            resp.raise_for_status()
            return resp.json()["info"]["version"]
        except Exception:
            return "1.41.0"

    def get_cached_data(self, source: str) -> Optional[Dict[str, Any]]:
        cache_file = self.cache_path / f"{source}.json"
        if cache_file.exists():
            try:
                return json.loads(cache_file.read_text()).get("data")
            except (json.JSONDecodeError, KeyError):
                pass
        return None

    def force_update(self) -> Dict[str, bool]:
        for cache_file in self.cache_path.glob("*.json"):
            try:
                cache_file.unlink()
            except OSError:
                pass
        return self.update_if_stale()

    def get_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {}
        for source_name, source_config in self.SOURCES.items():
            cache_file = self.cache_path / f"{source_name}.json"
            if cache_file.exists():
                try:
                    data = json.loads(cache_file.read_text())
                    status[source_name] = {
                        "cached": True,
                        "fetched_at": data.get("fetched_at"),
                        "valid": self._is_cache_valid(cache_file, source_config["cache_hours"]),
                    }
                except (json.JSONDecodeError, ValueError):
                    status[source_name] = {"cached": False, "valid": False}
            else:
                status[source_name] = {"cached": False, "valid": False}
        return status
