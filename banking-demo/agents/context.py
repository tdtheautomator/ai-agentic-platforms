"""
Agent context dataclass for banking-demo.

Immutable context passed between agents during pipeline execution.
Contains all necessary information for an agent to perform its task.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from llm.backend import LLMBackend
from memory.manager import MemoryManager


@dataclass(frozen=True)
class AgentContext:
    """
    Immutable context passed to agents during pipeline execution.
    
    Contains all dependencies and state needed for agents to execute
    their tasks. Frozen to prevent accidental mutations.
    
    Attributes:
        app_id: Unique application ID.
        customer: Customer profile dictionary.
        loan: Loan details dictionary.
        session_num: Current harness session number.
        memory_manager: Memory manager for all 4 stores.
        llm_client: LLM backend client.
        results: Dictionary of results from previous agents.
        request_id: Correlation ID for request tracing.
    """

    app_id: str
    customer: dict[str, Any]
    loan: dict[str, Any]
    session_num: int
    memory_manager: MemoryManager
    llm_client: LLMBackend
    results: dict[str, str] = field(default_factory=dict)
    request_id: str = ""

    def get_previous_result(self, agent_name: str) -> str | None:
        """
        Get the result from a previous agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'intake', 'risk').
            
        Returns:
            Result text from the agent, or None if not found.
        """
        return self.results.get(agent_name)

    def add_result(self, agent_name: str, result: str) -> None:
        """
        Add a result from the current agent.
        
        Note: This modifies the frozen dataclass's dict field.
        Use with caution.
        
        Args:
            agent_name: Name of the agent.
            result: Result text from the agent.
        """
        self.results[agent_name] = result
