"""
In-context memory store for banking-demo.

Stores conversation turns in a Python list with automatic compaction
when the limit is exceeded. Implements the MemoryStore interface.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from memory.base import MemoryStore

logger = structlog.get_logger(__name__)


class ContextMemory(MemoryStore):
    """
    In-context memory using a Python list.
    
    Stores conversation turns (messages) with automatic compaction
    when the context limit is exceeded. Compaction keeps system messages
    and the most recent turns, summarizing older turns.
    
    Attributes:
        data: List of message dictionaries.
        limit: Maximum number of turns before compaction (default: 10).
    """

    def __init__(self, limit: int = 10):
        """
        Initialize in-context memory.
        
        Args:
            limit: Maximum number of turns before compaction (default: 10).
        """
        self.data: list[dict[str, Any]] = []
        self.limit = limit
        self.compactions = 0

    @property
    def store_name(self) -> str:
        """Get store name."""
        return "context"

    async def add(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a message to context memory.
        
        Args:
            key: Message role (e.g., 'system', 'user', 'assistant').
            value: Message content.
            metadata: Optional metadata (ignored for context memory).
        """
        entry = {
            "role": key,
            "content": value,
            "ts": datetime.utcnow().strftime("%H:%M:%S"),
        }
        self.data.append(entry)

        await logger.ainfo(
            "context_memory_add",
            role=key,
            content_len=len(str(value)),
            total_turns=len(self.data),
        )

        # Check if compaction is needed
        if len(self.data) > self.limit:
            await self._compact()

    async def get(self, key: str) -> Any | None:
        """
        Get the last message with a given role.
        
        Args:
            key: Message role to search for.
            
        Returns:
            The last message with that role, or None if not found.
        """
        for entry in reversed(self.data):
            if entry["role"] == key:
                return entry["content"]
        return None

    async def search(
        self,
        query: str,
        top_k: int = 2,
    ) -> list[Any]:
        """
        Search context for messages containing query text.
        
        Args:
            query: Search query string.
            top_k: Maximum number of results.
            
        Returns:
            List of matching message contents.
        """
        results = []
        query_lower = query.lower()
        
        for entry in reversed(self.data):
            if query_lower in entry["content"].lower():
                results.append(entry["content"])
                if len(results) >= top_k:
                    break
        
        return results

    async def clear(self) -> None:
        """Clear all messages from context memory."""
        self.data.clear()
        self.compactions = 0
        await logger.ainfo("context_memory_cleared")

    async def count(self) -> int:
        """Get the number of messages in context."""
        return len(self.data)

    async def _compact(self) -> None:
        """
        Compact context by keeping system messages and recent turns.
        
        Keeps the first system message and the last 4 turns, summarizing
        the removed turns into a compaction notice.
        """
        before_count = len(self.data)

        # Keep system messages (first one only)
        system_msgs = [m for m in self.data if m["role"] == "system"][:1]

        # Add compaction summary
        summary = {
            "role": "system",
            "content": f"[COMPACTED] Prior context: {before_count - 4} turns about loan application processing.",
            "ts": datetime.utcnow().strftime("%H:%M:%S"),
        }
        system_msgs.append(summary)

        # Keep last 4 turns
        recent_turns = self.data[-4:]

        # Rebuild data
        self.data.clear()
        self.data.extend(system_msgs)
        self.data.extend(recent_turns)

        self.compactions += 1

        await logger.ainfo(
            "context_memory_compacted",
            before=before_count,
            after=len(self.data),
            compactions=self.compactions,
        )

    async def get_all(self) -> list[dict[str, Any]]:
        """
        Get all messages in context.
        
        Returns:
            List of all message dictionaries.
        """
        return self.data.copy()
