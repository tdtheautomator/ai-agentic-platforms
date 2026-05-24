"""
Decision agent for banking-demo.

Makes the final credit decision — approve, conditional approval,
or decline — with rationale.
"""

from __future__ import annotations

import time

import structlog

from agents.base import Agent
from agents.context import AgentContext
from agents.decision.prompts import SYSTEM_PROMPT, build_user_message, parse_decision

logger = structlog.get_logger(__name__)


class DecisionAgent(Agent):
    """
    Decision agent — final stage of the loan pipeline.
    
    Responsibilities:
    1. Combine all upstream assessments
    2. Call LLM for final decision
    3. Determine final status (approved, conditional, declined)
    4. Store decision in semantic memory
    5. Log to episodic memory
    6. Update application status
    """

    def __init__(self):
        """Initialize decision agent."""
        super().__init__("decision", SYSTEM_PROMPT)

    async def run(self, context: AgentContext) -> str:
        """
        Execute decision agent.
        
        Args:
            context: Agent context with customer, loan, and dependencies.
            
        Returns:
            Final decision from LLM.
        """
        start_time = time.perf_counter()

        try:
            await logger.ainfo(
                "agent_start",
                agent=self.name,
                app_id=context.app_id,
                request_id=context.request_id,
            )

            # Step 1: Get upstream results
            customer = context.customer
            loan = context.loan
            intake_result = context.get_previous_result("intake") or "Pending"
            risk_result = context.get_previous_result("risk") or "Pending"
            fraud_result = context.get_previous_result("fraud") or "Pending"

            # Step 2: Prepare message for LLM
            user_msg = build_user_message(
                customer, loan, context.app_id, intake_result, risk_result, fraud_result
            )

            # Step 3: Call LLM
            result = await context.llm_client.call(
                self.system_prompt,
                user_msg,
                max_tokens=100,
            )

            # Step 4: Determine final status
            final_status = parse_decision(result)

            # Step 5: Store decision in semantic memory
            await context.memory_manager.add_to_semantic(
                f"decision-{context.app_id}",
                f"Application {context.app_id}: {customer['name']} requested "
                f"£{loan['amount']:,}. Credit {customer['credit_score']}. "
                f"Decision: {final_status}. {result[:100]}",
                metadata={
                    "type": "decision",
                    "app_id": context.app_id,
                    "customer": customer["name"],
                    "outcome": final_status,
                },
            )

            # Step 6: Log to episodic memory
            await context.memory_manager.add_to_episodic(
                context.app_id,
                {
                    "app_id": context.app_id,
                    "session_num": context.session_num,
                    "agent": self.name,
                    "event": "decision_complete",
                    "detail": result[:120],
                    "outcome": final_status,
                },
            )

            # Step 7: Cache final decision in working memory
            await context.memory_manager.add_to_working(
                f"{context.app_id}:final_decision",
                result[:200],
                ttl=3600,
            )

            # Step 8: Add to context memory
            await context.memory_manager.add_to_context(
                "assistant",
                f"[Decision] {result}",
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
