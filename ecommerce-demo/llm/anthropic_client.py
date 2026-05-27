"""Anthropic LLM client."""

import httpx
from .backend import LLMBackend


class AnthropicClient(LLMBackend):
    """Anthropic LLM client."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001"):
        """
        Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key
            model: Model name
        """
        self.api_key = api_key
        self.model = model

    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        """Call Anthropic API."""
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
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
                        "messages": [{"role": "user", "content": user}],
                    },
                )
                return r.json()["content"][0]["text"].strip()
        except Exception as exc:
            print(f"[Anthropic] Error: {exc}")
            return ""

    def get_name(self) -> str:
        """Get backend name."""
        return "anthropic"

    def get_model(self) -> str:
        """Get model name."""
        return self.model
