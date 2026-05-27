"""LLM backend factory."""

import os
import httpx

from .backend import LLMBackend
from .mock_client import MockLLMClient
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient


class LLMFactory:
    """Factory for creating LLM backend instances."""

    @staticmethod
    async def create() -> LLMBackend:
        """
        Create LLM backend based on environment variables.
        
        Priority:
        1. OpenAI (if OPENAI_API_KEY set)
        2. Anthropic (if ANTHROPIC_API_KEY set)
        3. Ollama (if reachable)
        4. Mock (fallback)
        
        Returns:
            LLMBackend instance
        """
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
        ollama_model = (
            os.getenv("ECOMMERCE_OLLAMA_MODEL")
            or os.getenv("OLLAMA_MODEL")
            or "qwen3:0.6b"
        ).strip()

        if openai_key:
            return OpenAIClient(openai_key)

        if anthropic_key:
            return AnthropicClient(anthropic_key)

        # Check if Ollama is reachable
        if await LLMFactory._probe_ollama(ollama_host):
            return OllamaClient(ollama_host, ollama_model)

        return MockLLMClient()

    @staticmethod
    async def _probe_ollama(host: str) -> bool:
        """Check if Ollama is reachable."""
        try:
            async with httpx.AsyncClient(timeout=4) as c:
                r = await c.get(f"{host}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
