from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from log_parser.pipeline.db import TemplateDatabase


@dataclass
class TemplateStats:
    template_text: str
    usage_count: int = 0
    cache_count: int = 0
    slm_count: int = 0
    first_seen: str = ""
    last_used: str = ""
    example_log: str = ""

    def to_dict(self) -> dict:
        total = self.usage_count or 1
        return {
            "template_text": self.template_text,
            "usage_count": self.usage_count,
            "first_seen": self.first_seen,
            "last_used": self.last_used,
            "example_log": self.example_log,
            "source_ratio": {
                "cache_pct": round((self.cache_count / total) * 100, 2),
                "slm_pct": round((self.slm_count / total) * 100, 2),
            },
        }


@dataclass
class TemplateIntelligenceRegistry:
    """Tracks global template usage and source contribution ratios."""

    _stats: Dict[str, TemplateStats] = field(default_factory=dict)
    _lock: RLock = field(default_factory=RLock)
    _db: TemplateDatabase | None = field(default=None)

    def set_db(self, db: TemplateDatabase) -> None:
        """Set database instance for persistence."""
        self._db = db
        # Load existing stats from database
        self._load_from_db()

    def _load_from_db(self) -> None:
        """Load existing template stats from database."""
        if self._db is None:
            return
        
        try:
            stats_list = self._db.get_template_stats()
            with self._lock:
                for stat in stats_list:
                    template_text = stat["template_text"]
                    self._stats[template_text] = TemplateStats(
                        template_text=template_text,
                        usage_count=stat["usage_count"],
                        cache_count=stat["cache_count"],
                        slm_count=stat["slm_count"],
                        first_seen=stat["first_seen"],
                        last_used=stat["last_used"],
                    )
        except Exception as e:
            print(f"Warning: Failed to load template stats from database: {e}")

    def record(self, template: str, source: str, example_log: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        src = source.upper()
        with self._lock:
            if template not in self._stats:
                self._stats[template] = TemplateStats(template_text=template)

            stats = self._stats[template]
            if not stats.first_seen:
                stats.first_seen = now
            stats.usage_count += 1
            stats.last_used = now
            if not stats.example_log:
                stats.example_log = example_log

            if src == "CACHE":
                stats.cache_count += 1
            else:
                stats.slm_count += 1

        # Persist to database
        if self._db:
            try:
                self._db.save_template_stats(
                    template_text=template,
                    usage_count=self._stats[template].usage_count,
                    cache_count=self._stats[template].cache_count,
                    slm_count=self._stats[template].slm_count,
                    first_seen=self._stats[template].first_seen,
                    last_used=self._stats[template].last_used,
                )
            except Exception as e:
                print(f"Warning: Failed to save template stats to database: {e}")

    def snapshot(self) -> list[dict]:
        with self._lock:
            values = [s.to_dict() for s in self._stats.values()]
        values.sort(key=lambda item: item["usage_count"], reverse=True)
        return values
