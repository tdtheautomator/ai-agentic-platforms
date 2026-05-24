"""
Base Agent Class

Provides the base class for all agents in the pipeline.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from agents.context import AgentContext

logger = structlog.get_logger(__name__)


class Agent:
    """
    Base class for all agents in the pipeline.
    
    Provides common functionality for agent initialization and execution.
    """

    def __init__(self, name: str, system_prompt: str):
        """
        Initialize an agent.
        
        Args:
            name: Agent name (e.g., 'intake', 'risk', 'fraud', 'decision')
            system_prompt: System prompt for the LLM
        """
        self.name = name
        self.system_prompt = system_prompt

    async def run(self, context: AgentContext) -> str:
        """
        Execute the agent.
        
        Must be implemented by subclasses.
        
        Args:
            context: Agent execution context
            
        Returns:
            Agent result as a string
        """
        raise NotImplementedError(f"{self.__class__.__name__}.run() not implemented")

    async def _log_execution(
        self,
        context: AgentContext,
        duration_ms: float,
        status: str,
    ) -> None:
        """
        Log agent execution metrics.
        
        Args:
            context: Agent execution context
            duration_ms: Execution duration in milliseconds
            status: Execution status ('success' or 'error')
        """
        await logger.ainfo(
            "agent_execution",
            agent=self.name,
            app_id=context.app_id,
            request_id=context.request_id,
            duration_ms=duration_ms,
            status=status,
        )
