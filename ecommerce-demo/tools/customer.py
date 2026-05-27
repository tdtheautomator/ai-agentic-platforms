"""Customer-related tools."""

from .registry import register_tool
from data import CUSTOMERS


@register_tool
def get_customer(customer_id: str) -> dict:
    """Retrieve customer profile including tier, loyalty points, and fraud flag."""
    c = next((x for x in CUSTOMERS if x["id"] == customer_id), None)
    return c or {"error": "Customer not found"}


@register_tool
def verify_address(customer_id: str, address: str) -> dict:
    """Verify customer address matches profile."""
    c = next((x for x in CUSTOMERS if x["id"] == customer_id), None)
    if not c:
        return {"error": "Customer not found"}
    matches = c.get("address", "").lower() == address.lower()
    return {
        "customer_id": customer_id,
        "address_verified": matches,
        "stored_address": c.get("address"),
    }
