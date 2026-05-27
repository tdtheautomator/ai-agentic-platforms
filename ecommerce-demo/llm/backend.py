"""Base LLM backend interface."""

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Abstract base class for LLM backends."""

    @abstractmethod
    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        """
        Call the LLM with system and user messages.
        
        Args:
            system: System prompt
            user: User message
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get backend name."""
        pass

    @abstractmethod
    def get_model(self) -> str:
        """Get model name."""
        pass
