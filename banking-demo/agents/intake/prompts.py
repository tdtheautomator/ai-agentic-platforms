"""
Intake Agent Prompts

System prompts and message templates for the intake agent.
"""

SYSTEM_PROMPT = (
    "You are a banking intake specialist. You review loan applications concisely. "
    "Given a customer profile, KYC status, and affordability figures, write a 2-sentence "
    "intake summary noting: (1) whether the application is complete and (2) one key concern or positive. "
    "Be professional and factual. Do not make a final decision."
)


def build_user_message(customer: dict, loan: dict) -> str:
    """
    Build the user message for the intake agent.
    
    Args:
        customer: Customer profile dictionary
        loan: Loan details dictionary
        
    Returns:
        Formatted user message for the LLM
    """
    return (
        f"Customer {customer['name']}, credit {customer['credit_score']}, "
        f"income £{customer['income']:,}/yr. "
        f"Loan: £{loan['amount']:,} over {loan['term_months']}mo for '{loan['purpose']}'. "
        f"KYC: PASS. DTI: 35%. Monthly repayment: £450."
    )
