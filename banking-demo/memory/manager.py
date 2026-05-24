"""
Memory manager orchestrator for banking-demo.

Coordinates all 4 memory stores (context, episodic, semantic, working)
and provides a unified interface for the application.
"""

from __future__ import annotations

from typing import Any

import structlog

from memory.base import MemoryStore
from memory.context import ContextMemory
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.working import WorkingMemory

logger = structlog.get_logger(__name__)


class MemoryManager:
    """
    Orchestrates all 4 memory stores.
    
    Provides a unified interface for adding, retrieving, and searching
    across context, episodic, semantic, and working memory.
    
    Attributes:
        context: In-context memory store.
        episodic: Episodic (SQLite) memory store.
        semantic: Semantic (ChromaDB) memory store.
        working: Working (Redis) memory store.
    """

    def __init__(
        self,
        context: MemoryStore | None = None,
        episodic: MemoryStore | None = None,
        semantic: MemoryStore | None = None,
        working: MemoryStore | None = None,
    ):
        """
        Initialize memory manager with 4 stores.
        
        Args:
            context: In-context memory (default: new ContextMemory).
            episodic: Episodic memory (default: new EpisodicMemory).
            semantic: Semantic memory (default: new SemanticMemory).
            working: Working memory (default: new WorkingMemory).
        """
        self.context = context or ContextMemory()
        self.episodic = episodic or EpisodicMemory()
        self.semantic = semantic or SemanticMemory()
        self.working = working or WorkingMemory()

        self.stores = {
            "context": self.context,
            "episodic": self.episodic,
            "semantic": self.semantic,
            "working": self.working,
        }

    async def add_to_context(self, role: str, content: str) -> None:
        """
        Add a message to context memory.
        
        Args:
            role: Message role (system, user, assistant).
            content: Message content.
        """
        await self.context.add(role, content)

    async def add_to_episodic(
        self,
        app_id: str,
        event_data: dict[str, Any],
    ) -> None:
        """
        Log an event to episodic memory.
        
        Args:
            app_id: Application ID.
            event_data: Event details dict.
        """
        await self.episodic.add(app_id, event_data)

    async def add_to_semantic(
        self,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a document to semantic memory.
        
        Args:
            doc_id: Document ID.
            text: Document text to embed.
            metadata: Optional metadata.
        """
        await self.semantic.add(doc_id, text, metadata)

    async def add_to_working(
        self,
        key: str,
        value: Any,
        ttl: int = 120,
    ) -> None:
        """
        Cache a value in working memory.
        
        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (default: 120).
        """
        await self.working.add(key, value, metadata={"ttl": ttl})

    async def get_context(self, role: str) -> Any | None:
        """Get last message with given role from context."""
        return await self.context.get(role)

    async def get_episodic(self, app_id: str) -> Any | None:
        """Get first event for application from episodic."""
        return await self.episodic.get(app_id)

    async def get_semantic(self, doc_id: str) -> Any | None:
        """Get document from semantic memory."""
        return await self.semantic.get(doc_id)

    async def get_working(self, key: str) -> Any | None:
        """Get cached value from working memory."""
        return await self.working.get(key)

    async def search_context(self, query: str, top_k: int = 2) -> list[Any]:
        """Search context memory."""
        return await self.context.search(query, top_k)

    async def search_episodic(self, app_id: str, top_k: int = 10) -> list[Any]:
        """Search episodic memory for application events."""
        return await self.episodic.search(app_id, top_k)

    async def search_semantic(self, query: str, top_k: int = 2) -> list[Any]:
        """Search semantic memory by similarity."""
        return await self.semantic.search(query, top_k)

    async def clear_all(self) -> None:
        """Clear all memory stores."""
        for store in self.stores.values():
            await store.clear()
        await logger.ainfo("all_memory_stores_cleared")

    async def get_stats(self) -> dict[str, int]:
        """
        Get statistics for all memory stores.
        
        Returns:
            Dict with store names and item counts.
        """
        stats = {}
        for name, store in self.stores.items():
            try:
                stats[name] = await store.count()
            except Exception as exc:
                await logger.aerror(
                    "memory_stats_failed",
                    store=name,
                    error=str(exc),
                )
                stats[name] = 0
        return stats
