"""
Tests for configuration and data modules.

Tests settings loading, defaults, and data integrity.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from config import settings
from data.customers import CUSTOMERS
from data.rules import BANKING_RULES, FRAUD_SIGNALS


# ─────────────────────────────────────────────────────────────────
# Configuration Tests
# ─────────────────────────────────────────────────────────────────


def test_settings_defaults():
    """Test that settings have sensible defaults."""
    assert settings.ollama_host == "http://host.docker.internal:11434"
    assert settings.ollama_model == "qwen3:0.6b"
    assert settings.context_limit == 10
    assert settings.log_level == "INFO"


def test_settings_data_dir_exists():
    """Test that data directory path is valid."""
    assert isinstance(settings.data_dir, Path)


def test_settings_redis_url():
    """Test that Redis URL is configured."""
    assert settings.redis_url.startswith("redis://")


def test_settings_log_level_valid():
    """Test that log level is valid."""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert settings.log_level in valid_levels


# ─────────────────────────────────────────────────────────────────
# Customer Data Tests
# ─────────────────────────────────────────────────────────────────


def test_customers_not_empty():
    """Test that customer list is not empty."""
    assert len(CUSTOMERS) > 0


def test_customers_have_required_fields():
    """Test that each customer has required fields."""
    required_fields = ["id", "name", "credit_score", "income", "risk"]
    
    for customer in CUSTOMERS:
        for field in required_fields:
            assert field in customer
            assert customer[field] is not None


def test_customers_have_unique_ids():
    """Test that customer IDs are unique."""
    ids = [c["id"] for c in CUSTOMERS]
    assert len(ids) == len(set(ids))


def test_customers_credit_scores_valid():
    """Test that credit scores are in valid range."""
    for customer in CUSTOMERS:
        score = customer["credit_score"]
        assert 300 <= score <= 850  # Standard credit score range


def test_customers_risk_levels_valid():
    """Test that risk levels are valid."""
    valid_risks = ["LOW", "MEDIUM", "HIGH"]
    
    for customer in CUSTOMERS:
        assert customer["risk"] in valid_risks


# ─────────────────────────────────────────────────────────────────
# Banking Rules Tests
# ─────────────────────────────────────────────────────────────────


def test_banking_rules_not_empty():
    """Test that banking rules list is not empty."""
    assert len(BANKING_RULES) > 0


def test_banking_rules_are_strings():
    """Test that all rules are strings."""
    for rule in BANKING_RULES:
        assert isinstance(rule, str)
        assert len(rule) > 0


def test_banking_rules_contain_keywords():
    """Test that rules contain relevant keywords."""
    keywords = ["credit", "loan", "income", "DTI", "KYC", "fraud", "rate"]
    rule_text = " ".join(BANKING_RULES).lower()
    
    # At least some keywords should be present
    found_keywords = sum(1 for kw in keywords if kw.lower() in rule_text)
    assert found_keywords > 0


# ─────────────────────────────────────────────────────────────────
# Fraud Signals Tests
# ─────────────────────────────────────────────────────────────────


def test_fraud_signals_not_empty():
    """Test that fraud signals list is not empty."""
    assert len(FRAUD_SIGNALS) > 0


def test_fraud_signals_are_strings():
    """Test that all signals are strings."""
    for signal in FRAUD_SIGNALS:
        assert isinstance(signal, str)
        assert len(signal) > 0


def test_fraud_signals_describe_risks():
    """Test that signals describe fraud risks."""
    risk_keywords = ["fraud", "suspicious", "mismatch", "multiple", "unusual"]
    signal_text = " ".join(FRAUD_SIGNALS).lower()
    
    # Signals should describe fraud-related risks
    assert any(kw in signal_text for kw in risk_keywords)
