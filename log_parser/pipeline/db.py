from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Optional


class TemplateDatabase:
    """SQLite-based persistent storage for templates and cache data."""

    def __init__(self, db_path: str | Path = "log_parser/data/templates.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Cache entries table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    template_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_count INTEGER DEFAULT 0
                )
                """
            )

            # Template statistics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS template_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_text TEXT UNIQUE NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    cache_count INTEGER DEFAULT 0,
                    slm_count INTEGER DEFAULT 0,
                    first_seen TIMESTAMP,
                    last_used TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Tree history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tree_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tree_data TEXT NOT NULL,
                    batch_id INTEGER,
                    total_logs INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Example logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS example_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_text TEXT NOT NULL,
                    original_log TEXT NOT NULL,
                    log_level TEXT,
                    event_type TEXT,
                    source TEXT,
                    batch_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(template_text) REFERENCES template_stats(template_text)
                )
                """
            )

            conn.commit()
            conn.close()

    def cache_get(self, key: str) -> Optional[str]:
        """Get template from cache."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT template_text FROM cache_entries WHERE cache_key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return row["template_text"] if row else None

    def cache_set(self, key: str, template: str) -> None:
        """Store template in cache."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache_entries (cache_key, template_text, updated_at, hit_count)
                VALUES (?, ?, ?, (SELECT COALESCE(hit_count, 0) + 1 FROM cache_entries WHERE cache_key = ?))
                """,
                (key, template, now, key),
            )
            conn.commit()
            conn.close()

    def save_template_stats(
        self,
        template_text: str,
        usage_count: int,
        cache_count: int,
        slm_count: int,
        first_seen: str = "",
        last_used: str = "",
    ) -> None:
        """Save or update template statistics."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()

            cursor.execute(
                """
                INSERT OR REPLACE INTO template_stats
                (template_text, usage_count, cache_count, slm_count, first_seen, last_used, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (template_text, usage_count, cache_count, slm_count, first_seen, last_used, now),
            )
            conn.commit()
            conn.close()

    def get_template_stats(self) -> list[dict[str, Any]]:
        """Get all template statistics."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT template_text, usage_count, cache_count, slm_count, first_seen, last_used
                FROM template_stats
                ORDER BY usage_count DESC
                """
            )
            rows = cursor.fetchall()
            conn.close()
            return [
                {
                    "template_text": row["template_text"],
                    "usage_count": row["usage_count"],
                    "cache_count": row["cache_count"],
                    "slm_count": row["slm_count"],
                    "first_seen": row["first_seen"],
                    "last_used": row["last_used"],
                }
                for row in rows
            ]

    def save_example_log(
        self,
        template_text: str,
        original_log: str,
        log_level: str = "",
        event_type: str = "",
        source: str = "SLM",
        batch_id: int = 0,
    ) -> None:
        """Save example log entry."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO example_logs
                (template_text, original_log, log_level, event_type, source, batch_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (template_text, original_log, log_level, event_type, source, batch_id),
            )
            conn.commit()
            conn.close()

    def get_recent_examples(self, template_text: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get recent example logs for a template."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT original_log, log_level, event_type, source, batch_id, created_at
                FROM example_logs
                WHERE template_text = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (template_text, limit),
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]

    def save_tree_snapshot(
        self, tree_data: dict[str, Any], batch_id: int = 0, total_logs: int = 0
    ) -> None:
        """Save tree snapshot to history."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            tree_json = json.dumps(tree_data, default=str)
            cursor.execute(
                """
                INSERT INTO tree_history (tree_data, batch_id, total_logs)
                VALUES (?, ?, ?)
                """,
                (tree_json, batch_id, total_logs),
            )
            conn.commit()
            conn.close()

    def get_latest_tree_snapshot(self) -> Optional[dict[str, Any]]:
        """Get the most recent tree snapshot."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT tree_data FROM tree_history
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row["tree_data"])
            return None

    def get_all_cache_entries(self) -> dict[str, str]:
        """Get all cache entries for pre-loading."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT cache_key, template_text FROM cache_entries ORDER BY hit_count DESC")
            rows = cursor.fetchall()
            conn.close()
            return {row["cache_key"]: row["template_text"] for row in rows}

    def clear_old_entries(self, days: int = 30) -> int:
        """Clear cache entries older than specified days."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM cache_entries
                WHERE updated_at < datetime('now', '-' || ? || ' days')
                """,
                (days,),
            )
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted

    def flush(self) -> None:
        """Close and cleanup resources."""
        pass
