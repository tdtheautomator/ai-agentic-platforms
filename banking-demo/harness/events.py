"""
SSE event factory for banking-demo.

Creates Server-Sent Events (SSE) for streaming pipeline progress to clients.
Includes correlation ID support for request tracing.
"""

from __future__ import annotations

import json
from datetime import datetime


def make_event(
    kind: str,
    request_id: str = "",
    **kwargs,
) -> str:
    """
    Create a Server-Sent Event (SSE) message.
    
    Args:
        kind: Event type (e.g., 'harness_session', 'agent_start', 'done').
        request_id: Correlation ID for request tracing.
        **kwargs: Additional event data.
        
    Returns:
        SSE-formatted string (data: {...}\\n\\n).
    """
    event_data = {
        "kind": kind,
        "ts": datetime.utcnow().strftime("%H:%M:%S"),
        "request_id": request_id,
        **kwargs,
    }
    return f"data: {json.dumps(event_data)}\n\n"


def event_harness_session(
    session: int,
    session_type: str,
    msg: str,
    request_id: str = "",
) -> str:
    """Create a harness session event."""
    return make_event(
        "harness_session",
        request_id=request_id,
        session=session,
        type=session_type,
        msg=msg,
    )


def event_agent_start(
    agent: str,
    request_id: str = "",
) -> str:
    """Create an agent start event."""
    return make_event(
        "agent_start",
        request_id=request_id,
        agent=agent,
    )


def event_agent_complete(
    agent: str,
    result: str,
    request_id: str = "",
) -> str:
    """Create an agent complete event."""
    return make_event(
        "agent_complete",
        request_id=request_id,
        agent=agent,
        result=result,
    )


def event_memory_update(
    store: str,
    op: str,
    msg: str,
    request_id: str = "",
) -> str:
    """Create a memory update event."""
    return make_event(
        "memory",
        request_id=request_id,
        store=store,
        op=op,
        msg=msg,
    )


def event_compaction(
    before: int,
    after: int,
    msg: str,
    request_id: str = "",
) -> str:
    """Create a context compaction event."""
    return make_event(
        "harness_compaction",
        request_id=request_id,
        before=before,
        after=after,
        msg=msg,
    )


def event_done(
    app_id: str,
    customer: str,
    decision: str,
    sessions: int,
    agents_used: int,
    compactions: int,
    context_turns: int,
    results: dict,
    request_id: str = "",
) -> str:
    """Create a pipeline completion event."""
    return make_event(
        "done",
        request_id=request_id,
        app_id=app_id,
        customer=customer,
        decision=decision,
        sessions=sessions,
        agents_used=agents_used,
        compactions=compactions,
        context_turns=context_turns,
        results=results,
    )
