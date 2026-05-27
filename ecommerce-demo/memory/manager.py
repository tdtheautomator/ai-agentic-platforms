"""Memory manager coordinating all memory types."""

from pathlib import Path

from .context import ContextMemory
from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .working import WorkingMemory


class MemoryManager:
    """Manages all memory types."""

    def __init__(self, data_dir: Path):
        """
        Initialize memory manager.
        
        Args:
            data_dir: Base data directory
        """
        self.context = ContextMemory(limit=10)
        self.episodic = EpisodicMemory(data_dir / "sqlite" / "ecommerce.db")
        self.semantic = SemanticMemory(data_dir / "chroma")
        self.working = WorkingMemory()

    def get_context_for_llm(self) -> list[dict]:
        """Get context formatted for LLM."""
        return self.context.get_all()
