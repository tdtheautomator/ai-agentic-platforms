"""
Anthropic LLM backend implementation for banking-demo.

Uses the Anthropic API (Claude Haiku) for LLM calls.
"""

from __future__ import annotations

import httpx
import structlog

from llm.backend import LLMBackend

logger = structlog.get_logger(__name__)


class AnthropicClient(LLMBackend):
    """
    Anthropic LLM backend using Claude Haiku model.
    
    Attributes:
        api_key: Anthropic API key.
        model: Model name (default: claude-haiku-4-5-20251001).
        timeout: HTTP timeout in seconds (default: 60).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5-20251001",
        timeout: int = 60,
    ):
        """
        Initialize Anthropic backend.
        
        Args:
            api_key: Anthropic API key.
            model: Model name (default: claude-haiku-4-5-20251001).
            timeout: HTTP timeout in seconds (default: 60).
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "anthropic"

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
        Call Anthropic API.
        
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
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "system": system,
                        "messages": [
                            {"role": "user", "content": user},
                        ],
                    },
                )

                response.raise_for_status()
                result = response.json()["content"][0]["text"].strip()

                await logger.ainfo(
                    "anthropic_call_success",
                    model=self.model,
                    response_len=len(result),
                )

                return result

        except Exception as exc:
            await logger.aerror(
                "anthropic_call_failed",
                error=str(exc),
                model=self.model,
            )
            raise
