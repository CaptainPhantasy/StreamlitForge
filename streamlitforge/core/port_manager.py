"""Port Manager for deterministic, conflict-free port assignment.

Implements the algorithm from PLANNING.md:
1. Calculate deterministic port from project path hash
2. Check if port is available (socket probe)
3. If conflict, find nearest available port
4. Register port in ~/.streamlitforge/port_registry.json
"""

import hashlib
import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Dict, Optional


class NoPortsAvailableError(Exception):
    """Raised when no ports are available in the range."""
    pass


class PortManager:
    """Manages deterministic port assignment for Streamlit applications.

    Uses SHA-256 hashing of absolute project paths to assign ports,
    with conflict resolution and a persistent JSON registry.
    """

    BASE_PORT = 8501
    MAX_PORT = 8999
    REGISTRY_PATH = os.path.expanduser("~/.streamlitforge/port_registry.json")

    def __init__(self, base_port: int = BASE_PORT, max_port: int = MAX_PORT,
                 registry_path: Optional[str] = None):
        self.base_port = base_port
        self.max_port = max_port
        self.registry_path = registry_path or self.REGISTRY_PATH
        self._lock = threading.Lock()
        self._registry: Dict[str, dict] = {}
        self._load_registry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_port(self, project_path: str) -> int:
        """Return a deterministic, conflict-free port for *project_path*.

        If the project already has a registered port, return it.
        Otherwise compute one, resolve conflicts, register, and return.
        """
        project_path = os.path.realpath(project_path)

        with self._lock:
            # Already registered?
            for port_str, entry in self._registry.items():
                if entry.get("project_path") == project_path:
                    return int(port_str)

            # Deterministic hash
            deterministic_port = self._hash_path(project_path)

            if self._is_available(deterministic_port):
                self._register(deterministic_port, project_path)
                return deterministic_port

            # Conflict: find nearest available
            for offset in range(1, self.max_port - self.base_port + 1):
                for candidate in [deterministic_port + offset, deterministic_port - offset]:
                    if self.base_port <= candidate <= self.max_port and self._is_available(candidate):
                        self._register(candidate, project_path)
                        return candidate

            raise NoPortsAvailableError(
                f"No ports available in range {self.base_port}-{self.max_port}"
            )

    def release_port(self, project_path: str) -> bool:
        """Remove the registry entry for *project_path*."""
        project_path = os.path.realpath(project_path)
        with self._lock:
            to_remove = None
            for port_str, entry in self._registry.items():
                if entry.get("project_path") == project_path:
                    to_remove = port_str
                    break
            if to_remove:
                del self._registry[to_remove]
                self._save_registry()
                return True
            return False

    def lookup(self, project_path: str) -> Optional[int]:
        """Return the registered port for *project_path*, or None."""
        project_path = os.path.realpath(project_path)
        with self._lock:
            for port_str, entry in self._registry.items():
                if entry.get("project_path") == project_path:
                    return int(port_str)
            return None

    def heartbeat(self, project_path: str) -> None:
        """Update the last_heartbeat timestamp for a project."""
        project_path = os.path.realpath(project_path)
        with self._lock:
            for port_str, entry in self._registry.items():
                if entry.get("project_path") == project_path:
                    entry["last_heartbeat"] = _now_iso()
                    self._save_registry()
                    return

    def cleanup_stale(self, max_age_seconds: int = 3600) -> int:
        """Remove entries older than *max_age_seconds* without heartbeat.

        Returns the number of removed entries.
        """
        import datetime
        cutoff = time.time() - max_age_seconds
        removed = 0
        with self._lock:
            stale_keys = []
            for port_str, entry in self._registry.items():
                hb = entry.get("last_heartbeat") or entry.get("created", "")
                try:
                    ts = datetime.datetime.fromisoformat(hb).timestamp()
                except (ValueError, TypeError):
                    ts = 0
                if ts < cutoff:
                    stale_keys.append(port_str)
            for key in stale_keys:
                del self._registry[key]
                removed += 1
            if removed:
                self._save_registry()
        return removed

    def list_ports(self) -> Dict[str, dict]:
        """Return a copy of the full registry."""
        with self._lock:
            return dict(self._registry)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _hash_path(self, path: str) -> int:
        """Deterministic port from absolute path hash."""
        h = hashlib.sha256(path.encode()).hexdigest()
        return self.base_port + (int(h[:6], 16) % (self.max_port - self.base_port))

    def _is_available(self, port: int) -> bool:
        """Check the port is not in our registry and not bound on localhost."""
        if str(port) in self._registry:
            return False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False

    def _register(self, port: int, project_path: str) -> None:
        self._registry[str(port)] = {
            "project_path": project_path,
            "project_name": os.path.basename(project_path),
            "pid": os.getpid(),
            "last_heartbeat": _now_iso(),
            "created": _now_iso(),
        }
        self._save_registry()

    def _load_registry(self) -> None:
        path = Path(self.registry_path)
        if path.exists():
            try:
                self._registry = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._registry = {}
        else:
            self._registry = {}

    def _save_registry(self) -> None:
        path = Path(self.registry_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._registry, indent=2), encoding="utf-8")


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------

_global_port_manager: Optional[PortManager] = None
_global_lock = threading.Lock()


def get_port_manager(**kwargs) -> PortManager:
    """Return the global PortManager singleton."""
    global _global_port_manager
    if _global_port_manager is None:
        with _global_lock:
            if _global_port_manager is None:
                _global_port_manager = PortManager(**kwargs)
    return _global_port_manager


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _now_iso() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
