"""
Intake Agent

Collects and validates the initial loan application.
Performs KYC verification and affordability pre-check.
"""

from agents.intake.agent import IntakeAgent
from agents.intake.definition import intake_definition

__all__ = [
    "IntakeAgent",
    "intake_definition",
]
