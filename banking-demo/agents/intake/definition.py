"""
Intake Agent Definition

Defines the intake agent for the A2A protocol.
"""

from agents.registry import register_agent


@register_agent("intake")
def intake_definition() -> dict:
    """Intake agent definition."""
    return {
        "name": "Intake Agent",
        "description": "Collects and validates the initial loan application. Performs KYC and affordability pre-check.",
        "skills": ["loan_intake", "kyc_verification", "affordability_precheck"],
        "system_prompt": (
            "You are a banking intake specialist. You review loan applications concisely. "
            "Given a customer profile, KYC status, and affordability figures, write a 2-sentence "
            "intake summary noting: (1) whether the application is complete and (2) one key concern or positive. "
            "Be professional and factual. Do not make a final decision."
        ),
    }
