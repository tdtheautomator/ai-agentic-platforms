"""
Fraud agent for banking-demo.

Screens transaction history, device signals, and behavioural patterns
for fraud indicators.
"""

from __future__ import annotations

import time

import structlog

from agents.base import Agent
from agents.context import AgentContext
from agents.fraud.prompts import SYSTEM_PROMPT, build_user_message

logger = structlog.get_logger(__name__)


class FraudAgent(Agent):
    """
    Fraud agent — third stage of the loan pipeline.
    
    Responsibilities:
    1. Scan transaction history
    2. Check working memory for upstream risk level
    3. Call LLM for fraud assessment
    4. Log to episodic memory
    5. Check for context compaction trigger
    """

    def __init__(self):
        """Initialize fraud agent."""
        super().__init__("fraud", SYSTEM_PROMPT)

    async def run(self, context: AgentContext) -> str:
        """
        Execute fraud agent.
        
        Args:
            context: Agent context with customer, loan, and dependencies.
            
        Returns:
            Fraud assessment from LLM.
        """
        start_time = time.perf_counter()

        try:
            await logger.ainfo(
                "agent_start",
                agent=self.name,
                app_id=context.app_id,
                request_id=context.request_id,
            )

            # Step 1: Get customer data
            customer = context.customer

            # Step 2: Simulate transaction history scan
            fraud_flags = False
            declined_30d = 0
            foreign_tx = 2

            # Step 3: Check working memory for upstream risk level
            cached_risk = await context.memory_manager.get_working(
                f"{context.app_id}:risk_level"
            )

            # Step 4: Prepare message for LLM
            user_msg = build_user_message(customer, fraud_flags, declined_30d, foreign_tx, cached_risk)

            # Step 5: Call LLM
            result = await context.llm_client.call(
                self.system_prompt,
                user_msg,
                max_tokens=100,
            )

            # Step 6: Log to episodic memory
            await context.memory_manager.add_to_episodic(
                context.app_id,
                {
                    "app_id": context.app_id,
                    "session_num": context.session_num,
                    "agent": self.name,
                    "event": "fraud_complete",
                    "detail": f"flags={fraud_flags} signals=0",
                    "outcome": "complete",
                },
            )

            # Step 7: Add to context memory
            await context.memory_manager.add_to_context(
                "assistant",
                f"[Fraud] {result}",
            )

            duration_ms = (time.perf_counter() - start_time) * 1000
            await self._log_execution(context, duration_ms, "success")

            return result

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            await self._log_execution(context, duration_ms, "error")
            await logger.aerror(
                "agent_error",
                agent=self.name,
                error=str(exc),
                request_id=context.request_id,
            )
            raise
