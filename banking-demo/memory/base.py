"""
Abstract memory store interface for banking-demo.

Defines the contract for all memory store implementations (context, episodic,
semantic, working). Enables dependency injection and easy testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """
    Abstract base class for memory stores.
    
    All memory store implementations must inherit from this class and implement
    the core methods: add, get, search, clear, and count.
    """

    @abstractmethod
    async def add(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Store a value in memory.
        
        Args:
            key: Unique identifier for the value.
            value: The value to store.
            metadata: Optional metadata (e.g., source, timestamp, TTL).
            
        Raises:
            Exception: If storage fails.
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from memory.
        
        Args:
            key: Unique identifier for the value.
            
        Returns:
            The stored value, or None if not found.
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        top_k: int = 2,
    ) -> list[Any]:
        """
        Search memory for values matching a query.
        
        For semantic stores, this performs vector similarity search.
        For other stores, this may perform keyword matching.
        
        Args:
            query: Search query string.
            top_k: Maximum number of results to return.
            
        Returns:
            List of matching values (up to top_k items).
        """
        pass

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear all data from memory.
        
        Raises:
            Exception: If clearing fails.
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Get the number of items in memory.
        
        Returns:
            int: Number of stored items.
        """
        pass

    @property
    @abstractmethod
    def store_name(self) -> str:
        """
        Get the name of this memory store.
        
        Returns:
            str: Store name (e.g., 'context', 'episodic', 'semantic', 'working').
        """
        pass
