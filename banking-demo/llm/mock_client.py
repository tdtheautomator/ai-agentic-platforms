"""
Mock LLM backend for testing and offline mode.

Provides deterministic responses based on system prompt content.
Useful for development, testing, and when no real LLM is available.
"""

from __future__ import annotations

import structlog

from llm.backend import LLMBackend

logger = structlog.get_logger(__name__)


class MockLLMBackend(LLMBackend):
    """
    Mock LLM backend that returns deterministic responses.
    
    Responses are based on the content of the system prompt to simulate
    different agent behaviors (intake, risk, fraud, decision).
    """

    @property
    def backend_name(self) -> str:
        """Get backend name."""
        return "mock"

    @property
    def model_name(self) -> str:
        """Get model name."""
        return "mock"

    async def call(
        self,
        system: str,
        user: str,
        max_tokens: int = 400,
    ) -> str:
        """
        Return a deterministic mock response based on system prompt.
        
        Args:
            system: System prompt (used to determine response type).
            user: User message (parsed for context).
            max_tokens: Maximum tokens (ignored in mock mode).
            
        Returns:
            str: Deterministic mock response.
        """
        await logger.ainfo(
            "mock_llm_call",
            system_prompt_len=len(system),
            user_msg_len=len(user),
            max_tokens=max_tokens,
        )

        # Parse system prompt to determine agent type
        system_lower = system.lower()

        if "intake" in system_lower:
            return (
                "Application from Sarah Mitchell for £15,000 has been received and pre-screened. "
                "KYC documents are complete and verified; affordability pre-check passes with a DTI of 35%."
            )

        elif "risk" in system_lower:
            return (
                "Risk assessment: LOW risk. Credit score of 750 is above threshold; "
                "the primary factor is the applicant's strong credit profile."
            )

        elif "fraud" in system_lower:
            return (
                "No fraud indicators detected for Sarah Mitchell. "
                "Transaction history is consistent with normal customer behaviour — application may proceed."
            )

        elif "decision" in system_lower:
            return (
                "APPROVED: strong credit profile (score 750), manageable DTI (35%), and clean fraud screen."
            )

        else:
            return "Mock LLM response for testing."
