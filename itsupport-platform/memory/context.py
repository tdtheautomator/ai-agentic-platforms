"""
In-context memory management.

Stores conversation turns with automatic compaction when limit exceeded.
"""

from datetime import datetime

# Global state
_context: list[dict] = []
CTX_LIMIT: int = 10


def ctx_add(role: str, content: str) -> dict:
    """Add message to context with automatic compaction."""
    entry = {"role": role, "content": content,
             "ts": datetime.utcnow().strftime("%H:%M:%S")}
    _context.append(entry)
    if len(_context) > CTX_LIMIT:
        summary = f"[COMPACTED] Prior {len(_context)-4} turns: IT ticket intake and diagnostic in progress."
        kept = [m for m in _context if m["role"] == "system"][:1]
        kept.append({"role": "system", "content": summary, "ts": datetime.utcnow().strftime("%H:%M:%S")})
        kept.extend(_context[-4:])
        _context.clear()
        _context.extend(kept)
    return entry


def ctx_clear() -> None:
    """Clear all context."""
    _context.clear()
