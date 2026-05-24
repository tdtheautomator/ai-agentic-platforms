"""
Intake agent for banking-demo.

Collects and validates the initial loan application.
Performs KYC verification and affordability pre-check.
"""

from __future__ import annotations

import time

import structlog

from agents.base import Agent
from agents.context import AgentContext
from agents.intake.prompts import SYSTEM_PROMPT, build_user_message

logger = structlog.get_logger(__name__)


class IntakeAgent(Agent):
    """
    Intake agent — first stage of the loan pipeline.
    
    Responsibilities:
    1. Retrieve customer profile
    2. Verify KYC documents
    3. Calculate affordability
    4. Call LLM for intake assessment
    5. Log to episodic memory
    6. Cache in working memory
    """

    def __init__(self):
        """Initialize intake agent."""
        super().__init__("intake", SYSTEM_PROMPT)

    async def run(self, context: AgentContext) -> str:
        """
        Execute intake agent.
        
        Args:
            context: Agent context with customer, loan, and dependencies.
            
        Returns:
            Intake assessment from LLM.
        """
        start_time = time.perf_counter()

        try:
            await logger.ainfo(
                "agent_start",
                agent=self.name,
                app_id=context.app_id,
                request_id=context.request_id,
            )

            # Step 1: Build context from customer and loan data
            customer = context.customer
            loan = context.loan

            # Step 2: Prepare message for LLM
            user_msg = build_user_message(customer, loan)

            # Step 3: Call LLM
            result = await context.llm_client.call(
                self.system_prompt,
                user_msg,
                max_tokens=120,
            )

            # Step 4: Log to episodic memory
            await context.memory_manager.add_to_episodic(
                context.app_id,
                {
                    "app_id": context.app_id,
                    "session_num": context.session_num,
                    "agent": self.name,
                    "event": "intake_complete",
                    "detail": result[:120],
                    "outcome": "complete",
                },
            )

            # Step 5: Cache in working memory
            await context.memory_manager.add_to_working(
                f"{context.app_id}:intake_summary",
                result[:200],
                ttl=600,
            )

            # Step 6: Add to context memory
            await context.memory_manager.add_to_context(
                "assistant",
                f"[Intake] {result}",
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
