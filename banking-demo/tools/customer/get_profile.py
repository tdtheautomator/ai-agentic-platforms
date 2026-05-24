"""
Get Customer Profile Tool

Retrieves full customer profile including credit score and risk rating.
"""

from tools.registry import register_tool


# Import CUSTOMERS from main module (will be injected at runtime)
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS


@register_tool
def get_customer_profile(customer_id: str) -> dict:
    """Retrieve full customer profile including credit score and risk rating."""
    customers = _get_customers()
    c = next((x for x in customers if x["id"] == customer_id), None)
    return c or {"error": "Customer not found"}
