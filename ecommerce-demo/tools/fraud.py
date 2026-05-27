"""Fraud detection tools."""

from .registry import register_tool
from data import CUSTOMERS


@register_tool
def run_fraud_check(customer_id: str, order_total: float) -> dict:
    """Run automated fraud screening on the order using behavioural and order signals."""
    c = next((x for x in CUSTOMERS if x["id"] == customer_id), None)
    if not c:
        return {"error": "Customer not found"}
    flags = []
    if c["flagged"]:
        flags.append("customer previously flagged for suspicious activity")
    if c["orders_ytd"] < 2 and order_total > 200:
        flags.append("new customer placing high-value order")
    if order_total > 500 and c["tier"] == "bronze":
        flags.append("high-value order from low-tier account")
    return {
        "customer_id": customer_id,
        "fraud_score": min(len(flags) * 35, 95),
        "flags": flags,
        "requires_review": len(flags) > 0,
        "auto_approve": len(flags) == 0,
    }
