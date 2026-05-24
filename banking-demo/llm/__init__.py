"""
LLM backend module for banking-demo.

Provides pluggable LLM backends (OpenAI, Anthropic, Ollama, Mock)
with dependency injection and factory pattern.
"""

from llm.backend import LLMBackend
from llm.factory import resolve_llm_backend
from llm.mock_client import MockLLMBackend
from llm.openai_client import OpenAIClient
from llm.anthropic_client import AnthropicClient
from llm.ollama_client import OllamaClient

__all__ = [
    "LLMBackend",
    "resolve_llm_backend",
    "MockLLMBackend",
    "OpenAIClient",
    "AnthropicClient",
    "OllamaClient",
]
