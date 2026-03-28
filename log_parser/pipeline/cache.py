from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Dict, Optional

from log_parser.pipeline.db import TemplateDatabase


@dataclass
class CacheEntry:
    template: str


class TemplateCache:
    """Thread-safe in-memory + persistent cache for template reuse."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._store: Dict[str, CacheEntry] = {}
        self._lock = RLock()
        self._db: TemplateDatabase | None = None
        
        if db_path is None:
            db_path = "log_parser/data/templates.db"
        
        try:
            self._db = TemplateDatabase(db_path)
            # Pre-load cache from database
            self._load_from_db()
        except Exception as e:
            print(f"Warning: Failed to initialize database cache: {e}")
            self._db = None

    def _load_from_db(self) -> None:
        """Load all cache entries from database into memory."""
        if self._db is None:
            return
        
        try:
            entries = self._db.get_all_cache_entries()
            with self._lock:
                for key, template in entries.items():
                    self._store[key] = CacheEntry(template=template)
        except Exception as e:
            print(f"Warning: Failed to load cache from database: {e}")

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._store.get(key)
            return entry.template if entry else None

    def set(self, key: str, template: str) -> None:
        with self._lock:
            self._store[key] = CacheEntry(template=template)
        
        # Persist to database
        if self._db:
            try:
                self._db.cache_set(key, template)
            except Exception as e:
                print(f"Warning: Failed to persist cache entry to database: {e}")

    @staticmethod
    def key_from_signature(signature: str, batch_logs: list[str]) -> str:
        digest_input = signature + "||" + "\n".join(batch_logs)
        return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()
    
    def get_db(self) -> TemplateDatabase | None:
        """Get database instance for direct access."""
        return self._db
