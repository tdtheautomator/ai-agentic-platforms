"""OpenAI LLM client."""

import httpx
from .backend import LLMBackend


class OpenAIClient(LLMBackend):
    """OpenAI LLM client."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name
        """
        self.api_key = api_key
        self.model = model

    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        """Call OpenAI API."""
        try:
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
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
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            print(f"[OpenAI] Error: {exc}")
            return ""

    def get_name(self) -> str:
        """Get backend name."""
        return "openai"

    def get_model(self) -> str:
        """Get model name."""
        return self.model
