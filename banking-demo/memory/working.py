"""
Working memory store for banking-demo using Redis.

Stores temporary cache data with TTL (time-to-live). Falls back to
in-process dictionary if Redis is unavailable. Implements the MemoryStore interface.
"""

from __future__ import annotations

import time
from typing import Any

import structlog

from memory.base import MemoryStore

logger = structlog.get_logger(__name__)


class WorkingMemory(MemoryStore):
    """
    Working memory using Redis with in-process fallback.
    
    Stores temporary cache data with TTL support. If Redis is unavailable,
    falls back to an in-process dictionary with manual TTL expiration.
    
    Attributes:
        redis: Redis client (optional).
        fallback_store: In-process dictionary for when Redis is unavailable.
    """

    def __init__(self, redis_client: Any | None = None):
        """
        Initialize working memory.
        
        Args:
            redis_client: Optional Redis client. If None, uses in-process fallback.
        """
        self.redis = redis_client
        self.fallback_store: dict[str, dict[str, Any]] = {}

    @property
    def store_name(self) -> str:
        """Get store name."""
        return "working"

    async def add(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store a value with optional TTL.
        
        Args:
            key: Cache key.
            value: Value to cache.
            metadata: Optional metadata with 'ttl' key (seconds, default: 120).
        """
        ttl = (metadata or {}).get("ttl", 120) if metadata else 120

        try:
            if self.redis:
                # Use Redis with TTL
                self.redis.setex(f"bank:{key}", ttl, str(value))
            else:
                # Use fallback with manual expiration
                self.fallback_store[f"bank:{key}"] = {
                    "value": value,
                    "expiry": time.time() + ttl,
                }

            await logger.ainfo(
                "working_memory_add",
                key=key,
                ttl=ttl,
                backend="redis" if self.redis else "fallback",
            )

        except Exception as exc:
            await logger.aerror(
                "working_memory_add_failed",
                error=str(exc),
                key=key,
            )
            raise

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from cache.
        
        Args:
            key: Cache key.
            
        Returns:
            Cached value, or None if not found or expired.
        """
        try:
            if self.redis:
                # Get from Redis
                value = self.redis.get(f"bank:{key}")
                return value.decode() if value else None
            else:
                # Get from fallback
                entry = self.fallback_store.get(f"bank:{key}")
                if entry and time.time() < entry["expiry"]:
                    return entry["value"]
                # Clean up expired entry
                self.fallback_store.pop(f"bank:{key}", None)
                return None

        except Exception as exc:
            await logger.aerror(
                "working_memory_get_failed",
                error=str(exc),
                key=key,
            )
            raise

    async def search(
        self,
        query: str,
        top_k: int = 2,
    ) -> list[Any]:
        """
        Search working memory (limited implementation).
        
        Args:
            query: Search query (unused for working memory).
            top_k: Maximum number of results.
            
        Returns:
            Empty list (working memory doesn't support search).
        """
        return []

    async def clear(self) -> None:
        """Clear all cache entries."""
        try:
            if self.redis:
                # Clear Redis keys
                keys = self.redis.keys("bank:*")
                if keys:
                    self.redis.delete(*keys)
            else:
                # Clear fallback store
                self.fallback_store.clear()

            await logger.ainfo("working_memory_cleared")

        except Exception as exc:
            await logger.aerror(
                "working_memory_clear_failed",
                error=str(exc),
            )
            raise

    async def count(self) -> int:
        """Get the number of active cache entries."""
        try:
            if self.redis:
                keys = self.redis.keys("bank:*")
                return len(keys) if keys else 0
            else:
                # Count non-expired entries
                now = time.time()
                count = sum(
                    1 for entry in self.fallback_store.values()
                    if now < entry["expiry"]
                )
                return count

        except Exception as exc:
            await logger.aerror(
                "working_memory_count_failed",
                error=str(exc),
            )
            return 0

    async def list_all(self) -> list[dict[str, Any]]:
        """
        List all active cache entries.
        
        Returns:
            List of dicts with key, value, and TTL.
        """
        try:
            if self.redis:
                keys = self.redis.keys("bank:*")
                out = []
                for k in keys[:20]:  # Limit to 20 for performance
                    v = self.redis.get(k)
                    if v:
                        ttl = self.redis.ttl(k)
                        out.append({
                            "key": k.decode() if isinstance(k, bytes) else k,
                            "value": (v.decode() if isinstance(v, bytes) else v)[:80],
                            "ttl": ttl,
                        })
                return out
            else:
                # List fallback entries
                now = time.time()
                return [
                    {
                        "key": k,
                        "value": str(v["value"])[:80],
                        "ttl": int(v["expiry"] - now),
                    }
                    for k, v in self.fallback_store.items()
                    if now < v["expiry"]
                ]

        except Exception as exc:
            await logger.aerror(
                "working_memory_list_all_failed",
                error=str(exc),
            )
            return []
