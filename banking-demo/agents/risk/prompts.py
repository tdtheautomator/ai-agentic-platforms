"""
Risk Agent Prompts

System prompts and message templates for the risk assessment agent.
"""

SYSTEM_PROMPT = (
    "You are a credit risk analyst at a retail bank. "
    "Given a credit score, DTI ratio, income, and loan amount, write a 2-sentence risk assessment. "
    "State the risk level (LOW/MEDIUM/HIGH) and the single most important factor. "
    "Be concise and data-driven."
)


def build_user_message(customer: dict, loan: dict, rules: list[str]) -> str:
    """
    Build the user message for the risk agent.
    
    Args:
        customer: Customer profile dictionary
        loan: Loan details dictionary
        rules: List of relevant banking rules from semantic memory
        
    Returns:
        Formatted user message for the LLM
    """
    return (
        f"Credit score: {customer['credit_score']} (Excellent). "
        f"Annual income: £{customer['income']:,}. "
        f"Loan amount: £{loan['amount']:,}. "
        f"DTI ratio: 35% (pass). "
        f"Relevant rules: {rules[0] if rules else 'Standard criteria apply'}"
    )
