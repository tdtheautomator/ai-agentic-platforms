"""
Risk Agent Definition

Defines the risk assessment agent for the A2A protocol.
"""

from agents.registry import register_agent


@register_agent("risk")
def risk_definition() -> dict:
    """Risk assessment agent definition."""
    return {
        "name": "Risk Assessment Agent",
        "description": "Evaluates credit risk using bureau data, income verification, and debt-to-income ratio.",
        "skills": ["credit_risk", "dti_analysis", "income_verification"],
        "system_prompt": (
            "You are a credit risk analyst at a retail bank. "
            "Given a credit score, DTI ratio, income, and loan amount, write a 2-sentence risk assessment. "
            "State the risk level (LOW/MEDIUM/HIGH) and the single most important factor. "
            "Be concise and data-driven."
        ),
    }
