"""In-context memory management."""

from datetime import datetime
from typing import Optional


class ContextMemory:
    """In-context memory for active conversation turns."""

    def __init__(self, limit: int = 10):
        """
        Initialize context memory.
        
        Args:
            limit: Maximum number of turns before compaction
        """
        self._context: list[dict] = []
        self.limit = limit

    def add(self, role: str, content: str) -> dict:
        """
        Add a message to context.
        
        Args:
            role: Message role (system, user, assistant)
            content: Message content
            
        Returns:
            Added entry
        """
        entry = {
            "role": role,
            "content": content,
            "ts": datetime.utcnow().strftime("%H:%M:%S"),
        }
        self._context.append(entry)

        # Compact if needed
        if len(self._context) > self.limit:
            self._compact()

        return entry

    def _compact(self) -> None:
        """Compact context by summarizing old turns."""
        summary = f"[COMPACTED] Prior {len(self._context) - 4} turns: e-commerce order processing in progress."
        kept = [m for m in self._context if m["role"] == "system"][:1]
        kept.append({
            "role": "system",
            "content": summary,
            "ts": datetime.utcnow().strftime("%H:%M:%S"),
        })
        kept.extend(self._context[-4:])
        self._context.clear()
        self._context.extend(kept)

    def get_all(self) -> list[dict]:
        """Get all context entries."""
        return self._context.copy()

    def clear(self) -> None:
        """Clear all context."""
        self._context.clear()

    def count(self) -> int:
        """Get number of turns."""
        return len(self._context)
