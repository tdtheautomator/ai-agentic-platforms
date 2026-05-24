"""
Abstract LLM backend interface for banking-demo.

Defines the contract for all LLM backend implementations (OpenAI, Anthropic,
Ollama, Mock). Enables dependency injection and easy testing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMBackend(ABC):
    """
    Abstract base class for LLM backends.
    
    All LLM implementations must inherit from this class and implement
    the call() method.
    """

    @abstractmethod
    async def call(
        self,
        system: str,
        user: str,
        max_tokens: int = 400,
    ) -> str:
        """
        Call the LLM with a system prompt and user message.
        
        Args:
            system: System prompt (instructions for the LLM).
            user: User message (the actual question/prompt).
            max_tokens: Maximum tokens in the response (default: 400).
            
        Returns:
            str: The LLM's response text.
            
        Raises:
            Exception: If the LLM call fails or times out.
        """
        pass

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """
        Get the name of this backend.
        
        Returns:
            str: Backend name (e.g., 'openai', 'ollama', 'mock').
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the model name used by this backend.
        
        Returns:
            str: Model name (e.g., 'gpt-4o-mini', 'qwen3:0.6b').
        """
        pass
