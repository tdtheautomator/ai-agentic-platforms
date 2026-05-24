"""
Tools Module for Banking Demo

Provides composable tool implementations for the loan pipeline:
- Customer Tools: profile retrieval, KYC verification
- Credit Tools: credit score checks, affordability calculations
- Fraud Tools: transaction scanning, fraud pattern analysis
- Compliance Tools: regulatory rules queries

All tools are automatically registered via the @register_tool decorator
and exposed through the TOOLS registry for discovery and execution.
"""

from tools.registry import TOOLS, register_tool

# Import all tools to trigger registration
from tools.customer import get_customer_profile, verify_kyc_documents
from tools.credit import check_credit_score, calculate_affordability
from tools.fraud import scan_transaction_history
from tools.compliance import query_banking_rules

__all__ = [
    # Registry
    "TOOLS",
    "register_tool",
    # Customer tools
    "get_customer_profile",
    "verify_kyc_documents",
    # Credit tools
    "check_credit_score",
    "calculate_affordability",
    # Fraud tools
    "scan_transaction_history",
    # Compliance tools
    "query_banking_rules",
]
