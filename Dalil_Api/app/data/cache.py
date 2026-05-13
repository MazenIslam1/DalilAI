"""
Query Result Cache
==================
LRU cache for Gemini responses to avoid duplicate API calls.
Critical for staying within the free tier rate limits.
"""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional

from app.config import get_logger, get_settings
from app.utils.helpers import hash_query

logger = get_logger(__name__)
settings = get_settings()


class ResponseCache:
    """
    Thread-safe LRU cache with TTL for AI responses.
    Saves tokens and API calls by caching identical/similar queries.
    """

    def __init__(
        self,
        max_size: int = None,
        ttl_seconds: int = None,
    ):
        self.max_size = max_size or settings.MAX_CACHE_SIZE
        self.ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._lock = Lock()

    def get(self, query: str, dataset_id: str) -> Optional[str]:
        """Look up a cached response. Returns None on miss."""
        key = hash_query(query, dataset_id)

        with self._lock:
            if key not in self._cache:
                logger.debug("cache_miss", query_hash=key)
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl:
                del self._cache[key]
                logger.debug("cache_expired", query_hash=key)
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            logger.info("cache_hit", query_hash=key)
            return entry["response"]

    def put(self, query: str, dataset_id: str, response: str) -> None:
        """Store a response in the cache."""
        key = hash_query(query, dataset_id)

        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size:
                evicted_key, _ = self._cache.popitem(last=False)
                logger.debug("cache_evicted", evicted_key=evicted_key)

            self._cache[key] = {
                "response": response,
                "timestamp": time.time(),
            }
            logger.debug("cache_stored", query_hash=key)

    def clear(self) -> None:
        """Clear all cached responses."""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# Singleton cache instance
response_cache = ResponseCache()
