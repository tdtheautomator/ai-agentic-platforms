"""
Ollama LLM backend implementation for banking-demo.

Uses local Ollama instance for LLM calls. Ollama must be running
on the host at the configured endpoint.
"""

from __future__ import annotations

import httpx
import structlog

from llm.backend import LLMBackend

logger = structlog.get_logger(__name__)


class OllamaClient(LLMBackend):
    """
    Ollama LLM backend for local model inference.
    
    Attributes:
        host: Ollama server URL (default: http://host.docker.internal:11434).
        model: Model name (default: qwen3:0.6b).
        timeout: HTTP timeout in seconds (default: 120).
    """

    def __init__(
        self,
        host: str = "http://host.docker.internal:11434",
        model: str = "qwen3:0.6b",
        timeout: int = 120,
    ):
        """
        Initialize Ollama backend.
        
        Args:
            host: Ollama server URL.
            model: Model name.
            timeout: HTTP timeout in seconds (default: 120 for local inference).
        """
        self.host = host
        self.model = model
        self.timeout = timeout

    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "ollama"

    @property
    def model_name(self) -> str:
        """Get model name."""
        return self.model

    async def call(
        self,
        system: str,
        user: str,
        max_tokens: int = 400,
    ) -> str:
        """
        Call Ollama API.
        
        Args:
            system: System prompt.
            user: User message.
            max_tokens: Maximum tokens in response.
            
        Returns:
            str: LLM response.
            
        Raises:
            Exception: If API call fails.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "stream": False,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    },
                )

                response.raise_for_status()
                result = response.json()["message"]["content"].strip()

                await logger.ainfo(
                    "ollama_call_success",
                    model=self.model,
                    response_len=len(result),
                )

                return result

        except Exception as exc:
            await logger.aerror(
                "ollama_call_failed",
                error=str(exc),
                model=self.model,
                host=self.host,
            )
            raise
