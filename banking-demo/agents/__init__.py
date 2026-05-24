"""
Agents module for banking-demo.

Provides composable agent implementations for the loan pipeline:
- IntakeAgent: Collects and validates initial application
- RiskAgent: Evaluates credit risk
- FraudAgent: Screens for fraud indicators
- DecisionAgent: Makes final credit decision
"""

from agents.base import Agent
from agents.context import AgentContext
from agents.registry import A2A_AGENTS

# Import definitions to trigger registration
from agents.intake import IntakeAgent, intake_definition
from agents.risk import RiskAgent, risk_definition
from agents.fraud import FraudAgent, fraud_definition
from agents.decision import DecisionAgent, decision_definition

__all__ = [
    "Agent",
    "AgentContext",
    "A2A_AGENTS",
    "IntakeAgent",
    "RiskAgent",
    "FraudAgent",
    "DecisionAgent",
]
