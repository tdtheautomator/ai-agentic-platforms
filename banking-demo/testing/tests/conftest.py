"""
Shared pytest fixtures and configuration for banking-demo tests.

Provides mock implementations of LLM backends, memory stores, and
other dependencies for unit testing.
"""

import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest


# ─────────────────────────────────────────────────────────────────
# Event Loop Fixture
# ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async tests.
    
    Yields:
        asyncio.AbstractEventLoop: Event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ─────────────────────────────────────────────────────────────────
# Mock LLM Backend Fixtures
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def mock_llm_backend():
    """
    Mock LLM backend that returns deterministic responses.
    
    Returns:
        AsyncMock: Mock LLM backend with call() method.
    """
    backend = AsyncMock()
    backend.call.return_value = "Mock LLM response for testing"
    return backend


@pytest.fixture
async def mock_llm_backend_with_responses():
    """
    Mock LLM backend with predefined responses per agent.
    
    Returns:
        AsyncMock: Mock LLM backend with agent-specific responses.
    """
    backend = AsyncMock()
    
    async def call_side_effect(system: str, user: str, max_tokens: int = 400) -> str:
        """Return mock responses based on system prompt."""
        if "intake" in system.lower():
            return "Application received and pre-screened. KYC documents verified. Affordability passes with DTI of 35%."
        elif "risk" in system.lower():
            return "Risk assessment: LOW risk. Credit score of 750 is above threshold; primary factor is strong credit profile."
        elif "fraud" in system.lower():
            return "No fraud indicators detected. Transaction history is consistent with normal customer behaviour."
        elif "decision" in system.lower():
            return "APPROVED: strong credit profile (score 750), manageable DTI (35%), and clean fraud screen."
        return "Mock response"
    
    backend.call.side_effect = call_side_effect
    return backend


# ─────────────────────────────────────────────────────────────────
# Mock Memory Store Fixtures
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def mock_memory_manager():
    """
    Mock memory manager with all 4 memory stores.
    
    Returns:
        MagicMock: Mock memory manager with context, episodic, semantic, working stores.
    """
    manager = MagicMock()
    
    # Create async mocks for each store
    for store_name in ("context", "episodic", "semantic", "working"):
        store = AsyncMock()
        store.add = AsyncMock()
        store.get = AsyncMock(return_value=None)
        store.search = AsyncMock(return_value=[])
        store.clear = AsyncMock()
        store.count = AsyncMock(return_value=0)
        setattr(manager, store_name, store)
    
    return manager


@pytest.fixture
async def mock_context_memory():
    """
    Mock in-context memory store.
    
    Returns:
        AsyncMock: Mock context memory with add, get, search, clear, count methods.
    """
    memory = AsyncMock()
    memory.data = []
    memory.add = AsyncMock()
    memory.get = AsyncMock(return_value=None)
    memory.search = AsyncMock(return_value=[])
    memory.clear = AsyncMock()
    memory.count = AsyncMock(return_value=0)
    return memory


@pytest.fixture
async def mock_episodic_memory():
    """
    Mock episodic (SQLite) memory store.
    
    Returns:
        AsyncMock: Mock episodic memory with database operations.
    """
    memory = AsyncMock()
    memory.add = AsyncMock()
    memory.get = AsyncMock(return_value=None)
    memory.search = AsyncMock(return_value=[])
    memory.clear = AsyncMock()
    memory.count = AsyncMock(return_value=0)
    return memory


@pytest.fixture
async def mock_semantic_memory():
    """
    Mock semantic (ChromaDB) memory store.
    
    Returns:
        AsyncMock: Mock semantic memory with vector search.
    """
    memory = AsyncMock()
    memory.add = AsyncMock()
    memory.get = AsyncMock(return_value=None)
    memory.search = AsyncMock(return_value=["Debt-to-income ratio must not exceed 43%"])
    memory.clear = AsyncMock()
    memory.count = AsyncMock(return_value=0)
    return memory


@pytest.fixture
async def mock_working_memory():
    """
    Mock working (Redis) memory store.
    
    Returns:
        AsyncMock: Mock working memory with TTL support.
    """
    memory = AsyncMock()
    memory.add = AsyncMock()
    memory.get = AsyncMock(return_value=None)
    memory.search = AsyncMock(return_value=[])
    memory.clear = AsyncMock()
    memory.count = AsyncMock(return_value=0)
    return memory


# ─────────────────────────────────────────────────────────────────
# Mock Tool Registry Fixture
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def mock_tool_registry():
    """
    Mock tool registry with banking tools.
    
    Returns:
        MagicMock: Mock tool registry with tool methods.
    """
    registry = MagicMock()
    
    # Mock tool methods
    registry.get_customer_profile = AsyncMock(return_value={
        "id": "CUST001",
        "name": "Sarah Mitchell",
        "credit_score": 750,
        "income": 85000,
    })
    registry.check_credit_score = AsyncMock(return_value={
        "score": 750,
        "band": "Excellent",
        "bureau": "Experian (simulated)",
    })
    registry.calculate_affordability = AsyncMock(return_value={
        "monthly_payment": 450.0,
        "dti_ratio": 35.0,
        "dti_pass": True,
    })
    registry.scan_transaction_history = AsyncMock(return_value={
        "fraud_flags": False,
        "declined_30d": 0,
    })
    registry.verify_kyc_documents = AsyncMock(return_value={
        "kyc_pass": True,
        "biometric_match": True,
    })
    registry.query_banking_rules = AsyncMock(return_value=[
        "Debt-to-income ratio must not exceed 43% for conventional loans."
    ])
    
    return registry


# ─────────────────────────────────────────────────────────────────
# Sample Data Fixtures
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_customer():
    """
    Sample customer data for testing.
    
    Returns:
        dict: Customer profile with credit score and income.
    """
    return {
        "id": "CUST001",
        "name": "Sarah Mitchell",
        "credit_score": 750,
        "income": 85000,
        "account": "ACC-4821",
        "balance": 12400,
        "tx_count": 145,
        "risk": "LOW",
    }


@pytest.fixture
def sample_loan():
    """
    Sample loan application data for testing.
    
    Returns:
        dict: Loan details with amount, term, and purpose.
    """
    return {
        "amount": 15000,
        "term_months": 36,
        "purpose": "Home renovation — kitchen and bathroom upgrade",
    }


@pytest.fixture
def sample_app_id():
    """
    Sample application ID for testing.
    
    Returns:
        str: Formatted application ID.
    """
    return "LOAN-120530-001"


# ─────────────────────────────────────────────────────────────────
# Async Context Managers for Testing
# ─────────────────────────────────────────────────────────────────


@pytest.fixture
async def async_context():
    """
    Async context manager for resource cleanup in tests.
    
    Yields:
        dict: Context dictionary for test state.
    """
    context = {}
    yield context
    # Cleanup would go here
    context.clear()


# ─────────────────────────────────────────────────────────────────
# Pytest Configuration
# ─────────────────────────────────────────────────────────────────


def pytest_configure(config):
    """
    Configure pytest with custom markers.
    
    Args:
        config: Pytest config object.
    """
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
