"""
Harness module for banking-demo.

Provides pipeline orchestration, session state management, and SSE events
for streaming loan application processing.
"""

from harness.events import (
    make_event,
    event_harness_session,
    event_agent_start,
    event_agent_complete,
    event_memory_update,
    event_compaction,
    event_done,
)
from harness.session import SessionState
from harness.pipeline import Pipeline

__all__ = [
    "make_event",
    "event_harness_session",
    "event_agent_start",
    "event_agent_complete",
    "event_memory_update",
    "event_compaction",
    "event_done",
    "SessionState",
    "Pipeline",
]
