"""
A2A agent definitions for banking-demo.

Defines the 4 agents in the pipeline: intake, risk, fraud, decision.
These definitions are used for agent discovery and skill registration.
"""

from __future__ import annotations

# A2A Agent Definitions (from original main.py lines 421–466)
A2A_AGENTS = {
    "intake": {
        "name": "Intake Agent",
        "description": "Collects and validates the initial loan application. Performs KYC and affordability pre-check.",
        "skills": ["loan_intake", "kyc_verification", "affordability_precheck"],
        "system_prompt": (
            "You are a banking intake specialist. You review loan applications concisely. "
            "Given a customer profile, KYC status, and affordability figures, write a 2-sentence "
            "intake summary noting: (1) whether the application is complete and (2) one key concern or positive. "
            "Be professional and factual. Do not make a final decision."
        ),
    },
    "risk": {
        "name": "Risk Assessment Agent",
        "description": "Evaluates credit risk using bureau data, income verification, and debt-to-income ratio.",
        "skills": ["credit_risk", "dti_analysis", "income_verification"],
        "system_prompt": (
            "You are a credit risk analyst at a retail bank. "
            "Given a credit score, DTI ratio, income, and loan amount, write a 2-sentence risk assessment. "
            "State the risk level (LOW/MEDIUM/HIGH) and the single most important factor. "
            "Be concise and data-driven."
        ),
    },
    "fraud": {
        "name": "Fraud Detection Agent",
        "description": "Screens transaction history, device signals, and behavioural patterns for fraud indicators.",
        "skills": ["fraud_screening", "transaction_analysis", "aml_check"],
        "system_prompt": (
            "You are a fraud analyst at a retail bank. "
            "Given transaction data and fraud flags, write a 2-sentence fraud assessment. "
            "State whether the application should proceed, be flagged for review, or be blocked. "
            "Reference specific signals. Be direct."
        ),
    },
    "decision": {
        "name": "Decision Agent",
        "description": "Makes the final credit decision — approve, conditional approval, or decline — with rationale.",
        "skills": ["credit_decision", "offer_generation", "decline_reasoning"],
        "system_prompt": (
            "You are a senior lending manager at a retail bank. "
            "Given intake, risk, and fraud assessments, make a final 2-sentence loan decision. "
            "State clearly: APPROVED, CONDITIONALLY APPROVED, or DECLINED, with the primary reason. "
            "Be definitive and professional."
        ),
    },
}
