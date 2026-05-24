"""
Fraud Agent Definition

Defines the fraud detection agent for the A2A protocol.
"""

from agents.registry import register_agent


@register_agent("fraud")
def fraud_definition() -> dict:
    """Fraud detection agent definition."""
    return {
        "name": "Fraud Detection Agent",
        "description": "Screens transaction history, device signals, and behavioural patterns for fraud indicators.",
        "skills": ["fraud_screening", "transaction_analysis", "aml_check"],
        "system_prompt": (
            "You are a fraud analyst at a retail bank. "
            "Given transaction data and fraud flags, write a 2-sentence fraud assessment. "
            "State whether the application should proceed, be flagged for review, or be blocked. "
            "Reference specific signals. Be direct."
        ),
    }
