"""
Comprehensive unit tests for harness and pipeline.

Tests session state management, pipeline orchestration, and SSE events.
"""

from __future__ import annotations

import pytest
from datetime import datetime

from harness.session import SessionState
from harness.pipeline import Pipeline
from harness.events import (
    make_event,
    event_harness_session,
    event_agent_complete,
    event_done,
)


# ─────────────────────────────────────────────────────────────────
# Session State Tests
# ─────────────────────────────────────────────────────────────────


def test_session_state_init(sample_customer, sample_loan):
    """Test SessionState initialization."""
    session = SessionState(
        app_id="LOAN-001",
        session_num=1,
        customer=sample_customer,
        loan=sample_loan,
    )
    
    assert session.app_id == "LOAN-001"
    assert session.session_num == 1
    assert session.compactions == 0
    assert len(session.progress) == 0


def test_session_state_set_progress(sample_customer, sample_loan):
    """Test setting agent progress."""
    session = SessionState(
        app_id="LOAN-001",
        session_num=1,
        customer=sample_customer,
        loan=sample_loan,
    )
    
    session.set_agent_progress("intake", "complete")
    assert session.progress["intake"] == "complete"


def test_session_state_set_result(sample_customer, sample_loan):
    """Test setting agent result."""
    session = SessionState(
        app_id="LOAN-001",
        session_num=1,
        customer=sample_customer,
        loan=sample_loan,
    )
    
    session.set_agent_result("intake", "Application received")
    assert session.results["intake"] == "Application received"


def test_session_state_to_dict(sample_customer, sample_loan):
    """Test converting session to dictionary."""
    session = SessionState(
        app_id="LOAN-001",
        session_num=1,
        customer=sample_customer,
        loan=sample_loan,
    )
    
    session_dict = session.to_dict()
    
    assert session_dict["app_id"] == "LOAN-001"
    assert session_dict["session_num"] == 1
    assert "created_at" in session_dict
    assert "updated_at" in session_dict


# ─────────────────────────────────────────────────────────────────
# SSE Event Tests
# ─────────────────────────────────────────────────────────────────


def test_make_event():
    """Test creating a basic SSE event."""
    event = make_event("test_event", msg="Test message")
    
    assert "data:" in event
    assert "test_event" in event
    assert "Test message" in event
    assert event.endswith("\n\n")


def test_event_harness_session():
    """Test creating a harness session event."""
    event = event_harness_session(
        session=1,
        session_type="INITIALIZER",
        msg="Session started",
    )
    
    assert "harness_session" in event
    assert "INITIALIZER" in event
    assert "Session started" in event


def test_event_agent_complete():
    """Test creating an agent complete event."""
    event = event_agent_complete(
        agent="intake",
        result="Application received",
    )
    
    assert "agent_complete" in event
    assert "intake" in event
    assert "Application received" in event


def test_event_done():
    """Test creating a pipeline completion event."""
    event = event_done(
        app_id="LOAN-001",
        customer="Sarah Mitchell",
        decision="APPROVED",
        sessions=5,
        agents_used=4,
        compactions=0,
        context_turns=8,
        results={"intake": "OK", "risk": "LOW", "fraud": "OK", "decision": "APPROVED"},
    )
    
    assert "done" in event
    assert "LOAN-001" in event
    assert "APPROVED" in event
    assert "Sarah Mitchell" in event


# ─────────────────────────────────────────────────────────────────
# Pipeline Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_init(mock_memory_manager, mock_llm_backend):
    """Test Pipeline initialization."""
    pipeline = Pipeline(
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    assert len(pipeline.agents) == 4
    assert pipeline.agents[0].name == "intake"
    assert pipeline.agents[1].name == "risk"
    assert pipeline.agents[2].name == "fraud"
    assert pipeline.agents[3].name == "decision"


@pytest.mark.asyncio
async def test_pipeline_execute_yields_events(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test that pipeline yields SSE events."""
    pipeline = Pipeline(
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    events = []
    async for event in pipeline.execute(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
    ):
        events.append(event)
    
    # Should have multiple events
    assert len(events) > 0
    
    # First event should be harness_session
    assert "harness_session" in events[0]
    
    # Last event should be done
    assert "done" in events[-1]


@pytest.mark.asyncio
async def test_pipeline_execute_event_structure(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test that pipeline events have correct structure."""
    pipeline = Pipeline(
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    events = []
    async for event in pipeline.execute(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        request_id="req-123",
    ):
        events.append(event)
    
    # All events should be SSE-formatted
    for event in events:
        assert event.startswith("data:")
        assert event.endswith("\n\n")
        assert "req-123" in event  # Correlation ID should be present


@pytest.mark.asyncio
async def test_pipeline_execute_includes_agent_events(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test that pipeline includes agent execution events."""
    pipeline = Pipeline(
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    events_str = ""
    async for event in pipeline.execute(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
    ):
        events_str += event
    
    # Should include agent events
    assert "agent_start" in events_str or "agent_complete" in events_str


@pytest.mark.asyncio
async def test_pipeline_execute_includes_memory_events(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test that pipeline includes memory update events."""
    pipeline = Pipeline(
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    events_str = ""
    async for event in pipeline.execute(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
    ):
        events_str += event
    
    # Should include memory events
    assert "memory" in events_str or "episodic" in events_str


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_full_execution(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test full pipeline execution end-to-end."""
    pipeline = Pipeline(
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    event_count = 0
    final_event = None
    
    async for event in pipeline.execute(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
    ):
        event_count += 1
        final_event = event
    
    # Should have multiple events
    assert event_count > 0
    
    # Final event should be done
    assert final_event is not None
    assert "done" in final_event
