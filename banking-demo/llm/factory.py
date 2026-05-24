"""
Factory for resolving and creating LLM backends.

Implements auto-detection logic: tries OpenAI → Anthropic → Ollama → Mock.
"""

from __future__ import annotations

import os

import httpx
import structlog

from llm.backend import LLMBackend
from llm.mock_client import MockLLMBackend
from llm.openai_client import OpenAIClient
from llm.anthropic_client import AnthropicClient
from llm.ollama_client import OllamaClient

logger = structlog.get_logger(__name__)


async def _probe_ollama(host: str, timeout: int = 4) -> bool:
    """
    Probe if Ollama is reachable.
    
    Args:
        host: Ollama server URL.
        timeout: Probe timeout in seconds.
        
    Returns:
        bool: True if Ollama is reachable, False otherwise.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{host}/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def resolve_llm_backend() -> LLMBackend:
    """
    Auto-detect and return appropriate LLM backend.
    
    Resolution order:
    1. OpenAI (if OPENAI_API_KEY is set)
    2. Anthropic (if ANTHROPIC_API_KEY is set)
    3. Ollama (if reachable at OLLAMA_HOST)
    4. Mock (fallback)
    
    Returns:
        LLMBackend: Resolved backend instance.
    """
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    ollama_host = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:0.6b")

    # Try OpenAI
    if openai_key:
        await logger.ainfo("llm_backend_resolved", backend="openai")
        return OpenAIClient(api_key=openai_key)

    # Try Anthropic
    if anthropic_key:
        await logger.ainfo("llm_backend_resolved", backend="anthropic")
        return AnthropicClient(api_key=anthropic_key)

    # Try Ollama
    if await _probe_ollama(ollama_host):
        await logger.ainfo("llm_backend_resolved", backend="ollama", model=ollama_model)
        return OllamaClient(host=ollama_host, model=ollama_model)

    # Fallback to Mock
    await logger.awarning(
        "llm_backend_resolved",
        backend="mock",
        reason="No LLM backend available; using mock mode",
    )
    return MockLLMBackend()
