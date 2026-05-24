"""
Pipeline orchestrator for banking-demo.

Coordinates execution of all agents in sequence, manages session state,
and yields SSE events for client streaming.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import structlog

from agents.base import Agent
from agents.context import AgentContext
from agents.intake import IntakeAgent
from agents.risk import RiskAgent
from agents.fraud import FraudAgent
from agents.decision import DecisionAgent
from harness.events import (
    event_harness_session,
    event_agent_start,
    event_agent_complete,
    event_memory_update,
    event_compaction,
    event_done,
)
from harness.session import SessionState
from llm.backend import LLMBackend
from memory.manager import MemoryManager

logger = structlog.get_logger(__name__)


class Pipeline:
    """
    Loan application pipeline orchestrator.
    
    Coordinates execution of 4 agents (intake, risk, fraud, decision)
    in sequence, manages session state, and yields SSE events.
    
    Attributes:
        agents: List of agents to execute in order.
        memory_manager: Memory manager for all 4 stores.
        llm_client: LLM backend client.
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        llm_client: LLMBackend,
    ):
        """
        Initialize pipeline.
        
        Args:
            memory_manager: Memory manager instance.
            llm_client: LLM backend instance.
        """
        self.agents: list[Agent] = [
            IntakeAgent(),
            RiskAgent(),
            FraudAgent(),
            DecisionAgent(),
        ]
        self.memory_manager = memory_manager
        self.llm_client = llm_client

    async def execute(
        self,
        app_id: str,
        customer: dict,
        loan: dict,
        request_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Execute the loan pipeline.
        
        Yields SSE events as the pipeline progresses through all stages.
        
        Args:
            app_id: Unique application ID.
            customer: Customer profile.
            loan: Loan details.
            request_id: Correlation ID for request tracing.
            
        Yields:
            SSE event strings for client streaming.
        """
        # Initialize session
        session = SessionState(
            app_id=app_id,
            session_num=1,
            customer=customer,
            loan=loan,
        )

        # Initialize context memory
        await self.memory_manager.context.clear()
        await self.memory_manager.add_to_context(
            "system",
            f"Loan application session for {customer['name']} (ID: {app_id}). "
            f"Requested: £{loan['amount']:,} over {loan['term_months']} months.",
        )
        await self.memory_manager.add_to_context(
            "user",
            f"Process loan application. Customer: {customer['name']}, "
            f"Credit score: {customer['credit_score']}, Income: £{customer['income']:,}/yr.",
        )

        # Yield session initialization event
        session.session_num = 1
        yield event_harness_session(
            session=1,
            session_type="INITIALIZER",
            msg=f"Harness initialised for application {app_id}. "
            f"4 agent stages queued: intake → risk → fraud → decision.",
            request_id=request_id,
        )
        await asyncio.sleep(0.3)

        # Log application to episodic memory
        await self.memory_manager.add_to_episodic(
            app_id,
            {
                "app_id": app_id,
                "session_num": 1,
                "agent": "harness",
                "event": "application_created",
                "detail": f"£{loan['amount']:,} for {loan['purpose']}",
                "outcome": "submitted",
            },
        )

        yield event_memory_update(
            store="episodic",
            op="write",
            msg=f"[Episodic] Application {app_id} logged to audit trail (SQLite)",
            request_id=request_id,
        )
        await asyncio.sleep(0.3)

        # Execute each agent in sequence
        for idx, agent in enumerate(self.agents, start=2):
            session.session_num = idx
            
            # Yield session start event
            yield event_harness_session(
                session=idx,
                session_type="CODING_AGENT",
                msg=f"Harness reads progress: {', '.join(k + '=complete' for k in list(session.progress.keys())[:idx-2])}. "
                f"Next stage: {agent.name.upper()}.",
                request_id=request_id,
            )
            await asyncio.sleep(0.2)

            # Create agent context
            context = AgentContext(
                app_id=app_id,
                customer=customer,
                loan=loan,
                session_num=idx,
                memory_manager=self.memory_manager,
                llm_client=self.llm_client,
                results=session.results,
                request_id=request_id,
            )

            # Yield agent start event
            yield event_agent_start(agent=agent.name, request_id=request_id)
            await asyncio.sleep(0.1)

            # Execute agent
            try:
                result = await agent.run(context)
                session.set_agent_result(agent.name, result)
                session.set_agent_progress(agent.name, "complete")

                # Yield agent complete event
                yield event_agent_complete(
                    agent=agent.name,
                    result=result,
                    request_id=request_id,
                )

            except Exception as exc:
                await logger.aerror(
                    "agent_execution_failed",
                    agent=agent.name,
                    error=str(exc),
                    request_id=request_id,
                )
                session.set_agent_progress(agent.name, "error")
                raise

            await asyncio.sleep(0.3)

            # Check for context compaction
            ctx_count = await self.memory_manager.context.count()
            if ctx_count > 8:
                before = ctx_count
                await self.memory_manager.add_to_context(
                    "system",
                    "[COMPACTION TRIGGER]",
                )
                session.compactions += 1
                after = await self.memory_manager.context.count()

                yield event_compaction(
                    before=before,
                    after=after,
                    msg=f"[Harness] Context compacted: {before} → {after} turns. "
                    f"Session continuity maintained via progress file.",
                    request_id=request_id,
                )
                await asyncio.sleep(0.2)

        # Determine final decision
        decision_result = session.results.get("decision", "")
        decision_upper = decision_result.upper()
        
        if "APPROVED" in decision_upper and "CONDITIONAL" not in decision_upper:
            final_status = "APPROVED"
        elif "CONDITIONAL" in decision_upper:
            final_status = "CONDITIONAL"
        else:
            final_status = "DECLINED"

        # Yield completion event
        session.session_num = 5
        ctx_count = await self.memory_manager.context.count()
        
        yield event_done(
            app_id=app_id,
            customer=customer["name"],
            decision=final_status,
            sessions=5,
            agents_used=4,
            compactions=session.compactions,
            context_turns=ctx_count,
            results=session.results,
            request_id=request_id,
        )

        await logger.ainfo(
            "pipeline_complete",
            app_id=app_id,
            decision=final_status,
            request_id=request_id,
        )
