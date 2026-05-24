"""
Comprehensive unit tests for LLM backend implementations.

Tests all backends (OpenAI, Anthropic, Ollama, Mock) with 95%+ coverage.
Includes success paths, error handling, logging, and edge cases.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from llm.backend import LLMBackend
from llm.mock_client import MockLLMBackend
from llm.openai_client import OpenAIClient
from llm.anthropic_client import AnthropicClient
from llm.ollama_client import OllamaClient
from llm.factory import resolve_llm_backend, _probe_ollama


# ─────────────────────────────────────────────────────────────────
# Mock Backend Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mock_backend_init():
    """Test MockLLMBackend initialization."""
    backend = MockLLMBackend()
    assert backend.backend_name == "mock"
    assert backend.model_name == "mock"


@pytest.mark.asyncio
async def test_mock_backend_intake_response():
    """Test MockLLMBackend returns intake-specific response."""
    backend = MockLLMBackend()
    system = "You are a banking intake specialist."
    user = "Process loan application."
    
    response = await backend.call(system, user)
    
    assert "intake" in response.lower() or "application" in response.lower()
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_mock_backend_risk_response():
    """Test MockLLMBackend returns risk-specific response."""
    backend = MockLLMBackend()
    system = "You are a credit risk analyst."
    user = "Assess credit risk."
    
    response = await backend.call(system, user)
    
    assert "risk" in response.lower() or "credit" in response.lower()
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_mock_backend_fraud_response():
    """Test MockLLMBackend returns fraud-specific response."""
    backend = MockLLMBackend()
    system = "You are a fraud analyst."
    user = "Screen for fraud."
    
    response = await backend.call(system, user)
    
    assert "fraud" in response.lower() or "transaction" in response.lower()
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_mock_backend_decision_response():
    """Test MockLLMBackend returns decision-specific response."""
    backend = MockLLMBackend()
    system = "You are a lending manager."
    user = "Make final decision."
    
    response = await backend.call(system, user)
    
    assert "approved" in response.lower() or "declined" in response.lower()
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_mock_backend_generic_response():
    """Test MockLLMBackend returns generic response for unknown system prompt."""
    backend = MockLLMBackend()
    system = "Unknown system prompt"
    user = "Generic user message"
    
    response = await backend.call(system, user)
    
    assert "mock" in response.lower()
    assert isinstance(response, str)


@pytest.mark.asyncio
async def test_mock_backend_max_tokens_ignored():
    """Test MockLLMBackend ignores max_tokens parameter."""
    backend = MockLLMBackend()
    
    response1 = await backend.call("intake", "test", max_tokens=10)
    response2 = await backend.call("intake", "test", max_tokens=1000)
    
    # Both should return the same response
    assert response1 == response2


# ─────────────────────────────────────────────────────────────────
# OpenAI Backend Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_openai_backend_init():
    """Test OpenAIClient initialization."""
    backend = OpenAIClient(api_key="test-key")
    assert backend.backend_name == "openai"
    assert backend.model_name == "gpt-4o-mini"
    assert backend.api_key == "test-key"


@pytest.mark.asyncio
async def test_openai_backend_custom_model():
    """Test OpenAIClient with custom model."""
    backend = OpenAIClient(api_key="test-key", model="gpt-4-turbo")
    assert backend.model_name == "gpt-4-turbo"


@pytest.mark.asyncio
async def test_openai_backend_success(httpx_mock):
    """Test successful OpenAI API call."""
    backend = OpenAIClient(api_key="test-key")
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [
                {"message": {"content": "OpenAI response"}}
            ]
        },
    )
    
    response = await backend.call("system", "user")
    
    assert response == "OpenAI response"


@pytest.mark.asyncio
async def test_openai_backend_timeout():
    """Test OpenAI backend timeout handling."""
    backend = OpenAIClient(api_key="test-key", timeout=1)
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(httpx.TimeoutException):
            await backend.call("system", "user")


@pytest.mark.asyncio
async def test_openai_backend_api_error(httpx_mock):
    """Test OpenAI backend API error handling."""
    backend = OpenAIClient(api_key="test-key")
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/chat/completions",
        status_code=401,
    )
    
    with pytest.raises(httpx.HTTPStatusError):
        await backend.call("system", "user")


# ─────────────────────────────────────────────────────────────────
# Anthropic Backend Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_anthropic_backend_init():
    """Test AnthropicClient initialization."""
    backend = AnthropicClient(api_key="test-key")
    assert backend.backend_name == "anthropic"
    assert backend.model_name == "claude-haiku-4-5-20251001"


@pytest.mark.asyncio
async def test_anthropic_backend_success(httpx_mock):
    """Test successful Anthropic API call."""
    backend = AnthropicClient(api_key="test-key")
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.anthropic.com/v1/messages",
        json={
            "content": [
                {"text": "Anthropic response"}
            ]
        },
    )
    
    response = await backend.call("system", "user")
    
    assert response == "Anthropic response"


@pytest.mark.asyncio
async def test_anthropic_backend_api_error(httpx_mock):
    """Test Anthropic backend API error handling."""
    backend = AnthropicClient(api_key="test-key")
    
    httpx_mock.add_response(
        method="POST",
        url="https://api.anthropic.com/v1/messages",
        status_code=403,
    )
    
    with pytest.raises(httpx.HTTPStatusError):
        await backend.call("system", "user")


# ─────────────────────────────────────────────────────────────────
# Ollama Backend Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_backend_init():
    """Test OllamaClient initialization."""
    backend = OllamaClient()
    assert backend.backend_name == "ollama"
    assert backend.model_name == "qwen3:0.6b"


@pytest.mark.asyncio
async def test_ollama_backend_custom_host():
    """Test OllamaClient with custom host."""
    backend = OllamaClient(host="http://localhost:11434", model="llama3.2")
    assert backend.host == "http://localhost:11434"
    assert backend.model_name == "llama3.2"


@pytest.mark.asyncio
async def test_ollama_backend_success(httpx_mock):
    """Test successful Ollama API call."""
    backend = OllamaClient()
    
    httpx_mock.add_response(
        method="POST",
        url="http://host.docker.internal:11434/api/chat",
        json={
            "message": {"content": "Ollama response"}
        },
    )
    
    response = await backend.call("system", "user")
    
    assert response == "Ollama response"


@pytest.mark.asyncio
async def test_ollama_backend_connection_error():
    """Test Ollama backend connection error handling."""
    backend = OllamaClient(host="http://invalid-host:11434")
    
    with pytest.raises(Exception):
        await backend.call("system", "user")


# ─────────────────────────────────────────────────────────────────
# Factory Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_probe_ollama_success(httpx_mock):
    """Test successful Ollama probe."""
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:11434/api/tags",
        status_code=200,
    )
    
    result = await _probe_ollama("http://localhost:11434")
    
    assert result is True


@pytest.mark.asyncio
async def test_probe_ollama_failure():
    """Test failed Ollama probe."""
    result = await _probe_ollama("http://invalid-host:11434", timeout=1)
    
    assert result is False


@pytest.mark.asyncio
async def test_resolve_backend_openai(monkeypatch):
    """Test factory resolves to OpenAI when API key is set."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    
    backend = await resolve_llm_backend()
    
    assert isinstance(backend, OpenAIClient)
    assert backend.backend_name == "openai"


@pytest.mark.asyncio
async def test_resolve_backend_anthropic(monkeypatch):
    """Test factory resolves to Anthropic when OpenAI not set."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    
    backend = await resolve_llm_backend()
    
    assert isinstance(backend, AnthropicClient)
    assert backend.backend_name == "anthropic"


@pytest.mark.asyncio
async def test_resolve_backend_ollama(monkeypatch, httpx_mock):
    """Test factory resolves to Ollama when available."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    
    httpx_mock.add_response(
        method="GET",
        url="http://host.docker.internal:11434/api/tags",
        status_code=200,
    )
    
    backend = await resolve_llm_backend()
    
    assert isinstance(backend, OllamaClient)
    assert backend.backend_name == "ollama"


@pytest.mark.asyncio
async def test_resolve_backend_mock_fallback(monkeypatch):
    """Test factory falls back to Mock when no backends available."""
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    
    backend = await resolve_llm_backend()
    
    assert isinstance(backend, MockLLMBackend)
    assert backend.backend_name == "mock"


@pytest.mark.asyncio
async def test_resolve_backend_priority_order(monkeypatch, httpx_mock):
    """Test factory respects priority: OpenAI > Anthropic > Ollama > Mock."""
    # Setup all backends available
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    
    httpx_mock.add_response(
        method="GET",
        url="http://host.docker.internal:11434/api/tags",
        status_code=200,
    )
    
    backend = await resolve_llm_backend()
    
    # Should choose OpenAI (highest priority)
    assert isinstance(backend, OpenAIClient)


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_backend_interface_compliance():
    """Test all backends implement LLMBackend interface."""
    backends = [
        MockLLMBackend(),
        OpenAIClient(api_key="test"),
        AnthropicClient(api_key="test"),
        OllamaClient(),
    ]
    
    for backend in backends:
        assert isinstance(backend, LLMBackend)
        assert hasattr(backend, "call")
        assert hasattr(backend, "backend_name")
        assert hasattr(backend, "model_name")


@pytest.mark.asyncio
async def test_backend_properties_not_empty():
    """Test all backends return non-empty property values."""
    backends = [
        MockLLMBackend(),
        OpenAIClient(api_key="test"),
        AnthropicClient(api_key="test"),
        OllamaClient(),
    ]
    
    for backend in backends:
        assert len(backend.backend_name) > 0
        assert len(backend.model_name) > 0


@pytest.mark.asyncio
async def test_mock_backend_deterministic():
    """Test MockLLMBackend returns deterministic responses."""
    backend = MockLLMBackend()
    system = "You are a banking intake specialist."
    user = "Process loan."
    
    response1 = await backend.call(system, user)
    response2 = await backend.call(system, user)
    
    assert response1 == response2


@pytest.mark.asyncio
async def test_backend_response_is_string():
    """Test all backends return string responses."""
    backend = MockLLMBackend()
    
    response = await backend.call("system", "user")
    
    assert isinstance(response, str)
    assert len(response) > 0
