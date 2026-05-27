"""Ollama LLM client."""

import httpx
from .backend import LLMBackend


class OllamaClient(LLMBackend):
    """Ollama LLM client."""

    def __init__(self, host: str, model: str):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama host URL
            model: Model name
        """
        self.host = host
        self.model = model

    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        """Call Ollama API."""
        try:
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(
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
                return r.json()["message"]["content"].strip()
        except Exception as exc:
            print(f"[Ollama] Error: {exc}")
            return ""

    def get_name(self) -> str:
        """Get backend name."""
        return "ollama"

    def get_model(self) -> str:
        """Get model name."""
        return self.model
