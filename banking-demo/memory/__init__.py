"""
Memory module for banking-demo.

Provides 4 memory stores (context, episodic, semantic, working) with
unified interface and orchestration.
"""

from memory.base import MemoryStore
from memory.context import ContextMemory
from memory.episodic import EpisodicMemory
from memory.semantic import SemanticMemory
from memory.working import WorkingMemory
from memory.manager import MemoryManager

__all__ = [
    "MemoryStore",
    "ContextMemory",
    "EpisodicMemory",
    "SemanticMemory",
    "WorkingMemory",
    "MemoryManager",
]
