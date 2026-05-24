"""
Scan Transaction History Tool

Scans recent transactions for suspicious patterns and fraud indicators.
"""

from tools.registry import register_tool


# Import CUSTOMERS and FRAUD_SIGNALS from main module (will be injected at runtime)
def _get_customers():
    """Get customers list from main module."""
    from main import CUSTOMERS
    return CUSTOMERS


def _get_fraud_signals():
    """Get fraud signals list from main module."""
    from main import FRAUD_SIGNALS
    return FRAUD_SIGNALS


@register_tool
def scan_transaction_history(customer_id: str) -> dict:
    """Scan recent transactions for suspicious patterns."""
    customers = _get_customers()
    fraud_signals = _get_fraud_signals()
    
    c = next((x for x in customers if x["id"] == customer_id), None)
    if not c:
        return {"error": "Not found"}
    # Deterministic dummy data based on customer risk
    declined_count = {"LOW": 0, "MEDIUM": 1, "HIGH": 3}.get(c["risk"], 0)
    large_cash = {"LOW": 0, "MEDIUM": 0, "HIGH": 1}.get(c["risk"], 0)
    foreign_tx  = {"LOW": 2, "MEDIUM": 5, "HIGH": 8}.get(c["risk"], 0)
    return {
        "account": c["account"],
        "transactions_30d": c["tx_count"],
        "declined_30d": declined_count,
        "large_cash_deposits": large_cash,
        "foreign_transactions": foreign_tx,
        "fraud_flags": declined_count >= 3 or large_cash > 0,
        "flags": [s for i, s in enumerate(fraud_signals) if
                  (i == 0 and foreign_tx > 5) or (i == 2 and declined_count >= 3)],
    }
