"""
Harness — Session state management and pipeline orchestration.

Manages multi-session workflows with progress tracking and context compaction.
Orchestrates A2A agent collaboration with streaming SSE events.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import AsyncGenerator, Callable

from llm import _call_llm
from memory import ctx_add, ctx_clear, _context, CTX_LIMIT, epi_log, ticket_upsert, sem_add, work_set, work_get

# Global state
_SESSIONS: dict[str, dict] = {}


def _init_session(
    ticket_id: str,
    user: dict,
    ticket: dict,
    entity_name: str = "user",
    request_name: str = "ticket"
) -> dict:
    """Initialize session state."""
    state = {
        "ticket_id": ticket_id,
        "session_num": 0,
        "user": user,
        "ticket": ticket,
        "progress": {
            "triage": "pending",
            "diagnostic": "pending",
            "resolution": "pending",
            "escalation": "pending",
        },
        "results": {},
        "context_size": 0,
        "compactions": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _SESSIONS[ticket_id] = state
    return state


def _ev(kind: str, **kw) -> str:
    """Format SSE event."""
    return f"data: {json.dumps({'kind': kind, 'ts': datetime.utcnow().strftime('%H:%M:%S'), **kw})}\n\n"


async def _run_pipeline(
    ticket_id: str,
    user: dict,
    ticket: dict,
    agents_sequence: list[str],
    tools_dict: dict,
    agent_definitions: dict,
    mock_fn: Callable,
    config=None,
    entity_name: str = "user",
    request_name: str = "ticket",
    compaction_summary_template: str = "[COMPACTED] Prior {count} turns: IT ticket intake and diagnostic in progress.",
    pipeline_runs_counter=None,
    agent_latency_histogram=None,
) -> AsyncGenerator[str, None]:
    """Run multi-agent pipeline with streaming SSE events."""
    if pipeline_runs_counter:
        pipeline_runs_counter.inc()
    
    state = _init_session(ticket_id, user, ticket, entity_name, request_name)
    u = user
    tk = ticket

    # ── Session 1: Initializer ────────────────────────────────────────────────
    state["session_num"] = 1
    yield _ev("harness_session", session=1, type="INITIALIZER",
              msg=f"Harness initialised. Ticket {ticket_id} queued: {len(agents_sequence)} agent stages.")

    ticket_upsert({
        "id": ticket_id, "reporter": u["name"], "device": u["device"],
        "category": tk["category"], "priority": tk["priority"],
        "description": tk["description"], "status": "open",
        "os_version": u["os"], "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    })
    epi_log(ticket_id, 1, "harness", "ticket_created",
            f"{tk['priority']} {tk['category']}", "open")
    yield _ev("memory", store="episodic", op="write",
              msg=f"[Episodic] Ticket {ticket_id} created in SQLite audit log")
    await asyncio.sleep(0.3)

    ctx_add("system", f"IT support session for {u['name']} ({u['dept']}). "
                      f"Ticket {ticket_id}: {tk['category']}.")
    ctx_add("user", f"Issue: {tk['description'][:120]}")
    yield _ev("memory", store="context", op="write",
              msg=f"[In-Context] Session started — {len(_context)}/{CTX_LIMIT} turns",
              turns=len(_context), limit=CTX_LIMIT)
    await asyncio.sleep(0.3)

    # ── Sessions 2-5: Agent stages ────────────────────────────────────────────
    agent_results = {}
    compaction_event = None
    tools_called_count = 0

    for agent_idx, agent_id in enumerate(agents_sequence):
        session_num = agent_idx + 2
        state["session_num"] = session_num
        agent_def = agent_definitions.get(agent_id, {})

        yield _ev("harness_session", session=session_num, type="CODING_AGENT",
                  msg=f"Reading progress: {agent_id}. Dispatching via A2A.")
        yield _ev("a2a_discover", agent=agent_id,
                  card={"name": agent_def.get("name", agent_id),
                        "skills": agent_def.get("skills", [])},
                  msg=f"[A2A] Discovered {agent_def.get('name', agent_id)} Card")
        await asyncio.sleep(0.2)

        t0 = time.perf_counter()

        # ── Session 2: Triage Agent ───────────────────────────────────────────
        if agent_id == "triage":
            yield _ev("sdk_tool", tool="get_user_profile", msg="[SDK] get_user_profile()")
            profile = tools_dict["get_user_profile"]["fn"](u["id"])
            tools_called_count += 1
            yield _ev("sdk_result", tool="get_user_profile", result=str(profile)[:200])

            yield _ev("sdk_tool", tool="check_system_health", msg="[SDK] check_system_health()")
            health = tools_dict["check_system_health"]["fn"](u["id"], tk["category"])
            tools_called_count += 1
            yield _ev("sdk_result", tool="check_system_health", result=str(health)[:200])
            await asyncio.sleep(0.2)

            agent_msg = (
                f"Ticket {ticket_id} — User: {profile.get('name')} ({profile.get('dept')}), "
                f"Device: {profile.get('device')}, OS: {profile.get('os')}, Tier: {profile.get('tier')}.\n"
                f"Category: {tk['category']}, Priority: {tk['priority']}.\n"
                f"System health: {health}.\n"
                f"Issue: {tk['description'][:200]}"
            )

        # ── Session 3: Diagnostic Agent ───────────────────────────────────────
        elif agent_id == "diagnostic":
            yield _ev("sdk_tool", tool="check_system_health", msg="[SDK] check_system_health()")
            health = tools_dict["check_system_health"]["fn"](u["id"], tk["category"])
            tools_called_count += 1
            yield _ev("sdk_result", tool="check_system_health", result=str(health)[:200])

            yield _ev("sdk_tool", tool="check_similar_tickets", msg="[SDK] check_similar_tickets()")
            similar = tools_dict["check_similar_tickets"]["fn"](tk["category"])
            tools_called_count += 1
            yield _ev("sdk_result", tool="check_similar_tickets", result=str(similar)[:200])
            await asyncio.sleep(0.2)

            agent_msg = (
                f"Ticket {ticket_id} — Category: {tk['category']}, Priority: {tk['priority']}.\n"
                f"System diagnostics: {health}.\n"
                f"Similar tickets (last 24h): {similar['similar_24h']}, "
                f"Pattern detected: {similar['pattern_detected']}, "
                f"Potential outage: {similar['potential_outage']}, "
                f"Affected users: {similar['affected_users']}.\n"
                f"Recommendation: {similar['recommendation']}."
            )

        # ── Session 4: Resolution Agent ───────────────────────────────────────
        elif agent_id == "resolution":
            yield _ev("sdk_tool", tool="search_knowledge_base", msg="[SDK] search_knowledge_base()")
            kb_results = tools_dict["search_knowledge_base"]["fn"](f"{tk['category']} {tk['description'][:50]}")
            tools_called_count += 1
            yield _ev("sdk_result", tool="search_knowledge_base", result=str(kb_results)[:200])

            yield _ev("sdk_tool", tool="check_sla_status", msg="[SDK] check_sla_status()")
            sla = tools_dict["check_sla_status"]["fn"](tk["priority"], state["created_at"])
            tools_called_count += 1
            yield _ev("sdk_result", tool="check_sla_status", result=str(sla)[:200])
            await asyncio.sleep(0.2)

            agent_msg = (
                f"Ticket {ticket_id} — Category: {tk['category']}, Priority: {tk['priority']}.\n"
                f"Knowledge base articles: {kb_results}.\n"
                f"SLA status: elapsed {sla['elapsed_hours']}h, remaining {sla['remaining_hours']}h, "
                f"breached: {sla['sla_breached']}, warning: {sla['sla_warning']}.\n"
                f"Triage: {agent_results.get('triage', 'N/A')}\n"
                f"Diagnostic: {agent_results.get('diagnostic', 'N/A')}"
            )

        # ── Session 5: Escalation Agent (Hybrid) ─────────────────────────────
        elif agent_id == "escalation":
            yield _ev("sdk_tool", tool="check_sla_status", msg="[SDK] check_sla_status()")
            sla = tools_dict["check_sla_status"]["fn"](tk["priority"], state["created_at"])
            tools_called_count += 1
            yield _ev("sdk_result", tool="check_sla_status", result=str(sla)[:200])
            await asyncio.sleep(0.2)

            agent_msg = (
                f"Ticket {ticket_id} — Category: {tk['category']}, Priority: {tk['priority']}.\n"
                f"SLA: elapsed {sla['elapsed_hours']}h, remaining {sla['remaining_hours']}h, "
                f"breached: {sla['sla_breached']}, warning: {sla['sla_warning']}.\n"
                f"Triage: {agent_results.get('triage', 'N/A')}\n"
                f"Diagnostic: {agent_results.get('diagnostic', 'N/A')}\n"
                f"Resolution: {agent_results.get('resolution', 'N/A')}"
            )

        else:
            agent_msg = f"Process {ticket_id} for {agent_id} stage."

        yield _ev("a2a_request", agent=agent_id, method="tasks/send",
                  msg=f"[A2A] tasks/send → {agent_def.get('name', agent_id)}",
                  payload=agent_msg[:130])
        await asyncio.sleep(0.2)

        # Call LLM
        llm_response = await _call_llm(
            agent_def.get("system_prompt", ""),
            agent_msg,
            max_tokens=120,
            config=config
        )
        agent_output = llm_response or mock_fn(agent_id, {
            **u, "user_name": u["name"], "category": tk["category"],
            "priority": tk["priority"], "ticket_id": ticket_id
        })
        await asyncio.sleep(0.3)

        ctx_add("assistant", f"[{agent_id.capitalize()}] {agent_output}")
        state["results"][agent_id] = agent_output
        state["progress"][agent_id] = "complete"
        agent_results[agent_id] = agent_output

        if agent_latency_histogram:
            agent_latency_histogram.labels(agent=agent_id).observe(time.perf_counter() - t0)

        epi_log(ticket_id, session_num, agent_id, f"{agent_id}_complete", agent_output[:120], "complete")
        work_set(f"{ticket_id}:{agent_id}", agent_output[:200], ttl=600)

        yield _ev("a2a_response", agent=agent_id, status="completed", result=agent_output)
        yield _ev("memory", store="working", op="write",
                  msg=f"[Working] {agent_id} result cached in Redis (TTL 600s)")
        yield _ev("memory", store="context", op="write",
                  msg=f"[In-Context] {len(_context)}/{CTX_LIMIT} turns", turns=len(_context), limit=CTX_LIMIT)
        await asyncio.sleep(0.4)

        # Context compaction check
        if len(_context) >= CTX_LIMIT - 1 and not compaction_event:
            before = len(_context)
            ctx_add("system", "[COMPACTION]")
            compaction_event = (before, len(_context))
            state["compactions"] += 1
            yield _ev("harness_compaction",
                      msg=f"[Harness] Context compacted: {compaction_event[0]} → {compaction_event[1]} turns.",
                      before=compaction_event[0], after=compaction_event[1])

    # ── Final status determination ────────────────────────────────────────────
    # Parse escalation agent response to determine final status
    escalation_response = agent_results.get("escalation", "").upper()
    
    if "EMERGENCY PROTOCOL" in escalation_response:
        final_status = "emergency"
        escalation_level = "EMERGENCY"
    elif "ESCALATE L3" in escalation_response:
        final_status = "escalated_l3"
        escalation_level = "L3"
    elif "ESCALATE L2" in escalation_response:
        final_status = "escalated_l2"
        escalation_level = "L2"
    else:  # AUTO-RESOLVE or default
        final_status = "resolved"
        escalation_level = "NONE"
    
    yield _ev("escalation_decision", 
              level=escalation_level,
              response=agent_results.get("escalation", "")[:150],
              msg=f"[Escalation] Decision: {escalation_level}")
    
    # Store in semantic memory
    sem_add(
        f"Ticket {ticket_id}: {tk['category']} on {u['device']}. "
        f"Priority {tk['priority']}. Outcome: {final_status}. Escalation: {escalation_level}.",
        {"type": "decision", "ticket_id": ticket_id, "outcome": final_status, "escalation": escalation_level}
    )
    yield _ev("memory", store="semantic", op="write",
              msg="[Semantic] Ticket outcome stored in ChromaDB for future pattern matching")

    ticket_upsert({
        "id": ticket_id, "reporter": u["name"], "device": u["device"],
        "category": tk["category"], "priority": tk["priority"],
        "description": tk["description"], "status": final_status,
        "os_version": u["os"],
        "created_at": state["created_at"],
        "updated_at": datetime.utcnow().isoformat(),
    })
    work_set(f"{ticket_id}:final_status", final_status, ttl=3600)
    work_set(f"{ticket_id}:escalation_level", escalation_level, ttl=3600)

    yield _ev("memory", store="episodic", op="write",
              msg=f"[Episodic] Final status ({final_status.upper()}) with escalation {escalation_level} saved to audit log")
    yield _ev("memory", store="working", op="write",
              msg="[Working] Final status and escalation level cached in Redis (TTL 1hr) for notification service")
    await asyncio.sleep(0.3)

    # ── Pipeline complete ─────────────────────────────────────────────────────
    state["updated_at"] = datetime.utcnow().isoformat()

    yield _ev("done",
              ticket_id=ticket_id,
              reporter=u["name"],
              category=tk["category"],
              priority=tk["priority"],
              outcome=final_status.upper(),
              escalation_level=escalation_level,
              sessions=len(agents_sequence) + 1,
              compactions=state["compactions"],
              context_turns=len(_context),
              agents_used=len(agents_sequence),
              tools_called=tools_called_count,
              memory_stores=4,
              results=state["results"],
              msg=f"Pipeline complete. Outcome: {final_status.upper()}. Escalation: {escalation_level}.")
