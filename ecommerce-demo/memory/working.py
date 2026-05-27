"""Working memory management (Redis)."""

import os
import time
from typing import Optional


class WorkingMemory:
    """Working memory backed by Redis with in-process fallback."""

    def __init__(self):
        """Initialize working memory."""
        self._redis = None
        self._store: dict = {}
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis as rlib

            r = rlib.from_url(
                os.getenv("REDIS_URL", "redis://redis:6379"),
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            r.ping()
            self._redis = r
            print("[E-Commerce] Redis connected")
        except Exception as e:
            print(f"[E-Commerce] Redis offline — fallback: {e}")

    def set(self, key: str, value: str, ttl: int = 300) -> None:
        """
        Set a value.
        
        Args:
            key: Key
            value: Value
            ttl: Time to live in seconds
        """
        full_key = f"ec:{key}"
        if self._redis:
            self._redis.setex(full_key, ttl, value)
        else:
            self._store[full_key] = {"v": value, "exp": time.time() + ttl}

    def get(self, key: str) -> Optional[str]:
        """
        Get a value.
        
        Args:
            key: Key
            
        Returns:
            Value or None
        """
        full_key = f"ec:{key}"
        if self._redis:
            v = self._redis.get(full_key)
            return v.decode() if v else None
        e = self._store.get(full_key)
        if e and time.time() < e["exp"]:
            return e["v"]
        self._store.pop(full_key, None)
        return None

    def list_all(self) -> list[dict]:
        """
        List all items.
        
        Returns:
            List of items with key, value, ttl
        """
        if self._redis:
            keys = self._redis.keys("ec:*")
            return [
                {"key": k.decode(), "value": self._redis.get(k).decode()[:80], "ttl": self._redis.ttl(k)}
                for k in keys[:20]
                if self._redis.get(k)
            ]
        now = time.time()
        return [
            {"key": k, "value": v["v"][:80], "ttl": int(v["exp"] - now)}
            for k, v in self._store.items()
            if now < v["exp"]
        ]
