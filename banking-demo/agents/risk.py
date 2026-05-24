"""
Risk agent for banking-demo.

Evaluates credit risk using bureau data, income verification,
and debt-to-income ratio.
"""

from __future__ import annotations

import time

import structlog

from agents.base import Agent
from agents.context import AgentContext
from agents.risk.prompts import SYSTEM_PROMPT, build_user_message

logger = structlog.get_logger(__name__)


class RiskAgent(Agent):
    """
    Risk agent — second stage of the loan pipeline.
    
    Responsibilities:
    1. Query semantic memory for banking rules
    2. Analyze credit score and DTI
    3. Call LLM for risk assessment
    4. Log to episodic memory
    5. Cache risk level in working memory
    """

    def __init__(self):
        """Initialize risk agent."""
        super().__init__("risk", SYSTEM_PROMPT)

    async def run(self, context: AgentContext) -> str:
        """
        Execute risk agent.
        
        Args:
            context: Agent context with customer, loan, and dependencies.
            
        Returns:
            Risk assessment from LLM.
        """
        start_time = time.perf_counter()

        try:
            await logger.ainfo(
                "agent_start",
                agent=self.name,
                app_id=context.app_id,
                request_id=context.request_id,
            )

            # Step 1: Get customer and loan data
            customer = context.customer
            loan = context.loan

            # Step 2: Query semantic memory for relevant rules
            rules = await context.memory_manager.search_semantic(
                f"credit score {customer['credit_score']} DTI loan requirements",
                top_k=2,
            )

            # Step 3: Prepare message for LLM
            user_msg = build_user_message(customer, loan, rules)

            # Step 4: Call LLM
            result = await context.llm_client.call(
                self.system_prompt,
                user_msg,
                max_tokens=100,
            )

            # Step 5: Log to episodic memory
            await context.memory_manager.add_to_episodic(
                context.app_id,
                {
                    "app_id": context.app_id,
                    "session_num": context.session_num,
                    "agent": self.name,
                    "event": "risk_complete",
                    "detail": result[:120],
                    "outcome": "complete",
                },
            )

            # Step 6: Cache risk level in working memory
            risk_level = "LOW" if customer["credit_score"] >= 700 else "MEDIUM"
            await context.memory_manager.add_to_working(
                f"{context.app_id}:risk_level",
                risk_level,
                ttl=600,
            )

            # Step 7: Add to context memory
            await context.memory_manager.add_to_context(
                "assistant",
                f"[Risk] {result}",
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
