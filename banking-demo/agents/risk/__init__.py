"""
Risk Agent

Evaluates credit risk using bureau data, income verification,
and debt-to-income ratio.
"""

from agents.risk.agent import RiskAgent
from agents.risk.definition import risk_definition

__all__ = [
    "RiskAgent",
    "risk_definition",
]
