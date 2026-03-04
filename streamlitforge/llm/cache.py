"""SQLite response cache for LLM responses."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional


class ResponseCache:
    """SQLite-backed LLM response cache with TTL support."""

    def __init__(self, db_path: str = None, ttl_hours: int = 168):
        if db_path is None:
            db_path = str(Path.home() / ".streamlitforge" / "response_cache.db")
        self.db_path = db_path
        self.ttl_seconds = ttl_hours * 3600
        self._ensure_db()

    def _ensure_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    provider TEXT,
                    model TEXT,
                    tokens_used INTEGER,
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_created
                ON cache(created_at)
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    @staticmethod
    def _make_key(prompt: str, system_prompt: Optional[str] = None) -> str:
        combined = f"{system_prompt or ''}|||{prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def get(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        key = self._make_key(prompt, system_prompt)
        now = time.time()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT response, created_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            response, created_at = row
            if (now - created_at) > self.ttl_seconds:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                return None
            conn.execute(
                "UPDATE cache SET accessed_at = ?, access_count = access_count + 1 WHERE key = ?",
                (now, key),
            )
            return response

    def set(
        self,
        prompt: str,
        system_prompt: Optional[str],
        response: str,
        provider: str = "",
        model: str = "",
        tokens_used: int = 0,
    ):
        key = self._make_key(prompt, system_prompt)
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO cache
                   (key, response, provider, model, tokens_used, created_at, accessed_at, access_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (key, response, provider, model, tokens_used, now, now),
            )

    def clear(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM cache")

    def cleanup_expired(self) -> int:
        now = time.time()
        cutoff = now - self.ttl_seconds
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE created_at < ?", (cutoff,))
            return cursor.rowcount

    def get_stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            now = time.time()
            cutoff = now - self.ttl_seconds
            valid = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE created_at >= ?", (cutoff,)
            ).fetchone()[0]
            total_accesses = conn.execute(
                "SELECT COALESCE(SUM(access_count), 0) FROM cache"
            ).fetchone()[0]
        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": total - valid,
            "total_accesses": total_accesses,
            "db_path": self.db_path,
            "ttl_hours": self.ttl_seconds // 3600,
        }
