"""Tests for agents module."""

import pytest
from agents import A2A_AGENTS, get_mock_response


def test_agents_defined():
    """Test that all agents are defined."""
    assert "validation" in A2A_AGENTS
    assert "fulfilment" in A2A_AGENTS
    assert "pricing" in A2A_AGENTS
    assert "dispatch" in A2A_AGENTS


def test_agent_has_required_fields():
    """Test that agents have required fields."""
    for agent_id, agent in A2A_AGENTS.items():
        assert "name" in agent
        assert "description" in agent
        assert "skills" in agent
        assert "system_prompt" in agent


def test_mock_response_validation():
    """Test mock response for validation agent."""
    ctx = {
        "customer_name": "Test Customer",
        "tier": "gold",
        "fraud_requires_review": False,
        "all_available": True,
        "item_count": 2,
    }
    response = get_mock_response("validation", ctx)
    assert "Test Customer" in response
    assert "passes all validation checks" in response


def test_mock_response_dispatch():
    """Test mock response for dispatch agent."""
    ctx = {
        "customer_name": "Test Customer",
        "tier": "gold",
        "warehouse": "LDN-EAST",
        "fraud_requires_review": False,
        "all_available": True,
    }
    response = get_mock_response("dispatch", ctx)
    assert "CONFIRMED" in response
