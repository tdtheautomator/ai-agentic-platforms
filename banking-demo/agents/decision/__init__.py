"""
Decision Agent

Makes the final credit decision — approve, conditional approval,
or decline — with rationale.
"""

from agents.decision.agent import DecisionAgent
from agents.decision.definition import decision_definition

__all__ = [
    "DecisionAgent",
    "decision_definition",
]
