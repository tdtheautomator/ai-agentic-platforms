"""
OpenAI LLM backend implementation for banking-demo.

Uses the OpenAI API (gpt-4o-mini model) for LLM calls.
"""

from __future__ import annotations

import httpx
import structlog

from llm.backend import LLMBackend

logger = structlog.get_logger(__name__)


class OpenAIClient(LLMBackend):
    """
    OpenAI LLM backend using gpt-4o-mini model.
    
    Attributes:
        api_key: OpenAI API key.
        model: Model name (default: gpt-4o-mini).
        timeout: HTTP timeout in seconds (default: 60).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: int = 60,
    ):
        """
        Initialize OpenAI backend.
        
        Args:
            api_key: OpenAI API key.
            model: Model name (default: gpt-4o-mini).
            timeout: HTTP timeout in seconds (default: 60).
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "openai"

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
        Call OpenAI API.
        
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
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": max_tokens,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                    },
                )

                response.raise_for_status()
                result = response.json()["choices"][0]["message"]["content"].strip()

                await logger.ainfo(
                    "openai_call_success",
                    model=self.model,
                    response_len=len(result),
                )

                return result

        except Exception as exc:
            await logger.aerror(
                "openai_call_failed",
                error=str(exc),
                model=self.model,
            )
            raise
