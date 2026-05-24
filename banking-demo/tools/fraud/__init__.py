"""
Fraud Tools

Tools for fraud detection: transaction scanning, fraud pattern analysis.
"""

from tools.fraud.scan_transactions import scan_transaction_history

__all__ = [
    "scan_transaction_history",
]
