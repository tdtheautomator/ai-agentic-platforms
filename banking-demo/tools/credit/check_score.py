"""
Check Credit Score Tool

Runs a soft credit bureau enquiry and returns score plus band.
"""

from datetime import datetime
from tools.registry import register_tool


# Import CUSTOMERS from main module (will be injected at runtime)
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS


@register_tool
def check_credit_score(customer_id: str) -> dict:
    """Run a soft credit bureau enquiry and return score plus band."""
    customers = _get_customers()
    c = next((x for x in customers if x["id"] == customer_id), None)
    if not c:
        return {"error": "Not found"}
    score = c["credit_score"]
    band = "Excellent" if score >= 750 else "Good" if score >= 700 else \
           "Fair" if score >= 650 else "Poor" if score >= 600 else "Very Poor"
    return {"customer_id": customer_id, "score": score, "band": band,
            "bureau": "Experian (simulated)", "timestamp": datetime.utcnow().isoformat()}
