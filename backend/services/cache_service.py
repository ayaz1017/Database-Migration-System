"""
Lightweight in-memory TTL cache for API response caching.
Pure Python — no external dependencies (no Redis, no memcached).
"""

import hashlib
import json
import time
from threading import Lock


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL and tag-based invalidation."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._store: dict[str, dict] = {}  # key -> {"value": ..., "expires": float, "tags": set}
        self._lock = Lock()
        self.max_entries = max_entries

    def get(self, key: str):
        """Return cached value if key exists and hasn't expired, else None."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() > entry["expires"]:
                del self._store[key]
                return None
            return entry["value"]

    def _purge_expired_locked(self, now: float) -> None:
        """Helper to remove expired entries under lock."""
        expired = [k for k, v in self._store.items() if now > v["expires"]]
        for k in expired:
            del self._store[k]

    def set(self, key: str, value, ttl_seconds: float, tags: list[str] | None = None):
        """Store a value with a TTL. Optionally attach tags for bulk invalidation."""
        now = time.time()
        with self._lock:
            # Passive cleanup if store size is growing
            if len(self._store) >= self.max_entries // 2:
                self._purge_expired_locked(now)

            # Evict oldest entry if still exceeding max entries
            if len(self._store) >= self.max_entries:
                oldest_key = min(self._store.keys(), key=lambda k: self._store[k]["expires"])
                del self._store[oldest_key]

            self._store[key] = {
                "value": value,
                "expires": now + ttl_seconds,
                "tags": set(tags) if tags else set(),
            }

    def invalidate(self, key: str) -> None:
        """Remove a single key."""
        with self._lock:
            self._store.pop(key, None)

    def invalidate_tag(self, tag: str) -> None:
        """Remove all entries that carry the given tag."""
        with self._lock:
            keys_to_delete = [k for k, v in self._store.items() if tag in v["tags"]]
            for k in keys_to_delete:
                del self._store[k]

    def clear(self) -> None:
        """Flush the entire cache."""
        with self._lock:
            self._store.clear()

    @staticmethod
    def make_key(*parts) -> str:
        """Build a deterministic cache key from arbitrary parts."""
        raw = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]



cache = TTLCache()
