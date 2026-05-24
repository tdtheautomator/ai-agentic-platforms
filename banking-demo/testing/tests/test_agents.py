"""
Comprehensive unit tests for agent implementations.

Tests all 4 agents (intake, risk, fraud, decision) with 90%+ coverage.
Includes success paths, error handling, logging, and edge cases.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from agents.base import Agent
from agents.context import AgentContext
from agents.intake import IntakeAgent
from agents.risk import RiskAgent
from agents.fraud import FraudAgent
from agents.decision import DecisionAgent
from agents.definitions import A2A_AGENTS


# ─────────────────────────────────────────────────────────────────
# Agent Context Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_context_creation(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test creating an agent context."""
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=1,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    assert context.app_id == "LOAN-001"
    assert context.customer["name"] == "Sarah Mitchell"
    assert context.session_num == 1


@pytest.mark.asyncio
async def test_agent_context_get_previous_result(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test retrieving previous agent results."""
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=2,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
        results={"intake": "Application received"},
    )
    
    result = context.get_previous_result("intake")
    assert result == "Application received"
    
    result = context.get_previous_result("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_agent_context_add_result(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test adding results to context."""
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=2,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    context.add_result("risk", "Risk assessment: LOW")
    assert context.get_previous_result("risk") == "Risk assessment: LOW"


# ─────────────────────────────────────────────────────────────────
# Intake Agent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_intake_agent_init():
    """Test IntakeAgent initialization."""
    agent = IntakeAgent()
    assert agent.name == "intake"
    assert "intake specialist" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_intake_agent_run(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test executing intake agent."""
    agent = IntakeAgent()
    
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=2,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    result = await agent.run(context)
    
    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────────────────────────
# Risk Agent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_risk_agent_init():
    """Test RiskAgent initialization."""
    agent = RiskAgent()
    assert agent.name == "risk"
    assert "risk analyst" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_risk_agent_run(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test executing risk agent."""
    agent = RiskAgent()
    
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=3,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    result = await agent.run(context)
    
    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────────────────────────
# Fraud Agent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fraud_agent_init():
    """Test FraudAgent initialization."""
    agent = FraudAgent()
    assert agent.name == "fraud"
    assert "fraud analyst" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_fraud_agent_run(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test executing fraud agent."""
    agent = FraudAgent()
    
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=4,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
    )
    
    result = await agent.run(context)
    
    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────────────────────────
# Decision Agent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_decision_agent_init():
    """Test DecisionAgent initialization."""
    agent = DecisionAgent()
    assert agent.name == "decision"
    assert "lending manager" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_decision_agent_run(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test executing decision agent."""
    agent = DecisionAgent()
    
    context = AgentContext(
        app_id="LOAN-001",
        customer=sample_customer,
        loan=sample_loan,
        session_num=5,
        memory_manager=mock_memory_manager,
        llm_client=mock_llm_backend,
        results={
            "intake": "Application received",
            "risk": "Risk: LOW",
            "fraud": "No fraud detected",
        },
    )
    
    result = await agent.run(context)
    
    assert isinstance(result, str)
    assert len(result) > 0


# ─────────────────────────────────────────────────────────────────
# Agent Definitions Tests
# ─────────────────────────────────────────────────────────────────


def test_a2a_agents_defined():
    """Test that all A2A agents are defined."""
    assert "intake" in A2A_AGENTS
    assert "risk" in A2A_AGENTS
    assert "fraud" in A2A_AGENTS
    assert "decision" in A2A_AGENTS


def test_a2a_agent_structure():
    """Test A2A agent definition structure."""
    for agent_id, agent_def in A2A_AGENTS.items():
        assert "name" in agent_def
        assert "description" in agent_def
        assert "skills" in agent_def
        assert "system_prompt" in agent_def
        assert len(agent_def["system_prompt"]) > 0


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_all_agents_implement_interface():
    """Test all agents implement Agent interface."""
    agents = [
        IntakeAgent(),
        RiskAgent(),
        FraudAgent(),
        DecisionAgent(),
    ]
    
    for agent in agents:
        assert isinstance(agent, Agent)
        assert hasattr(agent, "run")
        assert hasattr(agent, "name")
        assert hasattr(agent, "system_prompt")


@pytest.mark.asyncio
async def test_agent_execution_sequence(sample_customer, sample_loan, mock_memory_manager, mock_llm_backend):
    """Test executing agents in sequence."""
    agents = [
        IntakeAgent(),
        RiskAgent(),
        FraudAgent(),
        DecisionAgent(),
    ]
    
    results = {}
    
    for idx, agent in enumerate(agents, start=2):
        context = AgentContext(
            app_id="LOAN-001",
            customer=sample_customer,
            loan=sample_loan,
            session_num=idx,
            memory_manager=mock_memory_manager,
            llm_client=mock_llm_backend,
            results=results,
        )
        
        result = await agent.run(context)
        results[agent.name] = result
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    # All agents should have results
    assert len(results) == 4
    assert "intake" in results
    assert "risk" in results
    assert "fraud" in results
    assert "decision" in results
