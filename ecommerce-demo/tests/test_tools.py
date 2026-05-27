"""Tests for tools module."""

import pytest
from tools import (
    get_customer,
    check_inventory,
    apply_promotions,
    calculate_shipping,
    run_fraud_check,
)


def test_get_customer():
    """Test customer retrieval."""
    result = get_customer("C001")
    assert result["id"] == "C001"
    assert result["name"] == "Lena Fischer"
    assert result["tier"] == "gold"


def test_get_customer_not_found():
    """Test customer not found."""
    result = get_customer("INVALID")
    assert "error" in result


def test_check_inventory():
    """Test inventory check."""
    result = check_inventory("SKU-001", 1)
    assert result["sku"] == "SKU-001"
    assert result["available"] is True
    assert "stock" in result


def test_check_inventory_not_found():
    """Test inventory not found."""
    result = check_inventory("INVALID-SKU", 1)
    assert "error" in result


def test_apply_promotions():
    """Test promotion application."""
    result = apply_promotions("C001", 100.0, "Electronics")
    assert "promo_code" in result
    assert "saving" in result
    assert result["customer_tier"] == "gold"


def test_calculate_shipping():
    """Test shipping calculation."""
    result = calculate_shipping("LDN-EAST", "SW1A", 1.0, 100.0)
    assert result["warehouse"] == "LDN-EAST"
    assert "standard_cost" in result
    assert "free_shipping" in result


def test_run_fraud_check():
    """Test fraud check."""
    result = run_fraud_check("C001", 100.0)
    assert result["customer_id"] == "C001"
    assert "fraud_score" in result
    assert "flags" in result
