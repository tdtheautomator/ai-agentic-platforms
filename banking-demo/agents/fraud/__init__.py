"""
Fraud Agent

Screens transaction history, device signals, and behavioural patterns
for fraud indicators.
"""

from agents.fraud.agent import FraudAgent
from agents.fraud.definition import fraud_definition

__all__ = [
    "FraudAgent",
    "fraud_definition",
]
