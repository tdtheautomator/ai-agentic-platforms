"""
Decision Agent Definition

Defines the decision agent for the A2A protocol.
"""

from agents.registry import register_agent


@register_agent("decision")
def decision_definition() -> dict:
    """Decision agent definition."""
    return {
        "name": "Decision Agent",
        "description": "Makes the final credit decision — approve, conditional approval, or decline — with rationale.",
        "skills": ["credit_decision", "offer_generation", "decline_reasoning"],
        "system_prompt": (
            "You are a senior lending manager at a retail bank. "
            "Given intake, risk, and fraud assessments, make a final 2-sentence loan decision. "
            "State clearly: APPROVED, CONDITIONALLY APPROVED, or DECLINED, with the primary reason. "
            "Be definitive and professional."
        ),
    }
