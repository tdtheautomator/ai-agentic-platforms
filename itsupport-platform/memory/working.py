"""
Working memory — Redis cache with in-process fallback.

Stores temporary data with TTL for cross-session communication.
Falls back to in-process dict if Redis unavailable.
"""

import time

# Module-level state
_redis = None
_store: dict = {}
_key_prefix: str = "it:"


def _init_redis(redis_url: str, key_prefix: str = "it:") -> None:
    """Initialize Redis connection with fallback."""
    global _redis, _key_prefix
    _key_prefix = key_prefix
    try:
        import redis as rlib
        r = rlib.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        _redis = r
        print("[IT Support] Redis connected")
    except Exception as e:
        print(f"[IT Support] Redis offline — in-process fallback: {e}")


def work_set(key: str, value: str, ttl: int = 300) -> None:
    """Set key in cache with TTL."""
    if _redis:
        _redis.setex(f"{_key_prefix}{key}", ttl, value)
    else:
        _store[f"{_key_prefix}{key}"] = {"v": value, "exp": time.time() + ttl}


def work_get(key: str) -> str | None:
    """Get key from cache."""
    if _redis:
        v = _redis.get(f"{_key_prefix}{key}")
        return v.decode() if v else None
    entry = _store.get(f"{_key_prefix}{key}")
    if entry and time.time() < entry["exp"]:
        return entry["v"]
    _store.pop(f"{_key_prefix}{key}", None)
    return None


def work_list() -> list[dict]:
    """List all cached keys."""
    if _redis:
        keys = _redis.keys(f"{_key_prefix}*")
        out = []
        for k in keys[:20]:
            v = _redis.get(k)
            if v:
                out.append({"key": k.decode(), "value": v.decode()[:80],
                            "ttl": _redis.ttl(k)})
        return out
    now = time.time()
    return [{"key": k, "value": v["v"][:80], "ttl": int(v["exp"]-now)}
            for k, v in _store.items() if now < v["exp"]]
