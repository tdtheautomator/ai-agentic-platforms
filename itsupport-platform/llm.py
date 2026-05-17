"""
LLM backend resolution and API calls.

Supports OpenAI, Anthropic, Ollama, and mock (fallback) backends.
Backend resolution order: OpenAI → Anthropic → Ollama → Mock
"""

import httpx

from config import Config

# Global state
_llm_backend: str = "mock"
_llm_model: str = "mock"


async def _probe_ollama(ollama_host: str) -> bool:
    """Check if Ollama is available at the given host."""
    try:
        async with httpx.AsyncClient(timeout=4) as c:
            r = await c.get(f"{ollama_host}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def _resolve_backend(config: Config) -> None:
    """Resolve LLM backend in order: OpenAI → Anthropic → Ollama → Mock."""
    global _llm_backend, _llm_model
    if config.OPENAI_API_KEY:
        _llm_backend, _llm_model = "openai", "gpt-4o-mini"
    elif config.ANTHROPIC_API_KEY:
        _llm_backend, _llm_model = "anthropic", "claude-haiku-4-5-20251001"
    elif await _probe_ollama(config.OLLAMA_HOST):
        _llm_backend, _llm_model = "ollama", config.OLLAMA_MODEL
    else:
        _llm_backend, _llm_model = "mock", "mock"
    print(f"[{config.SERVICE_NAME}] LLM: {_llm_backend}/{_llm_model}")


async def _call_llm(system: str, user: str, max_tokens: int = 350, config: Config = None) -> str:
    """Call LLM with fallback to mock on error."""
    try:
        if _llm_backend == "openai":
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}",
                             "Content-Type": "application/json"},
                    json={"model": _llm_model, "max_tokens": max_tokens,
                          "messages": [{"role": "system", "content": system},
                                       {"role": "user", "content": user}]},
                )
                return r.json()["choices"][0]["message"]["content"].strip()
        if _llm_backend == "anthropic":
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": config.ANTHROPIC_API_KEY,
                             "anthropic-version": "2023-06-01",
                             "Content-Type": "application/json"},
                    json={"model": _llm_model, "max_tokens": max_tokens,
                          "system": system,
                          "messages": [{"role": "user", "content": user}]},
                )
                return r.json()["content"][0]["text"].strip()
        if _llm_backend == "ollama":
            async with httpx.AsyncClient(timeout=120) as c:
                r = await c.post(
                    f"{config.OLLAMA_HOST}/api/chat",
                    json={"model": _llm_model, "stream": False,
                          "messages": [{"role": "system", "content": system},
                                       {"role": "user", "content": user}]},
                )
                return r.json()["message"]["content"].strip()
    except Exception as exc:
        print(f"[{config.SERVICE_NAME}] _call_llm ({_llm_backend}): {exc}")
    return ""
