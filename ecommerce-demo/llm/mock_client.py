"""Mock LLM client for testing."""

from .backend import LLMBackend


class MockLLMClient(LLMBackend):
    """Mock LLM client that returns deterministic responses."""

    async def call(self, system: str, user: str, max_tokens: int = 350) -> str:
        """Return empty string to trigger fallback to mock responses."""
        return ""

    def get_name(self) -> str:
        """Get backend name."""
        return "mock"

    def get_model(self) -> str:
        """Get model name."""
        return "mock"
