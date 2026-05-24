"""
Decision Agent Prompts

System prompts and message templates for the decision agent.
"""

SYSTEM_PROMPT = (
    "You are a senior lending manager at a retail bank. "
    "Given intake, risk, and fraud assessments, make a final 2-sentence loan decision. "
    "State clearly: APPROVED, CONDITIONALLY APPROVED, or DECLINED, with the primary reason. "
    "Be definitive and professional."
)


def build_user_message(
    customer: dict,
    loan: dict,
    app_id: str,
    intake_result: str,
    risk_result: str,
    fraud_result: str,
) -> str:
    """
    Build the user message for the decision agent.
    
    Args:
        customer: Customer profile dictionary
        loan: Loan details dictionary
        app_id: Application ID
        intake_result: Result from intake agent
        risk_result: Result from risk agent
        fraud_result: Result from fraud agent
        
    Returns:
        Formatted user message for the LLM
    """
    return (
        f"All upstream assessments complete for {customer['name']} "
        f"(ID: {app_id}). "
        f"Loan: £{loan['amount']:,} over {loan['term_months']} months. "
        f"INTAKE: {intake_result[:100]}. "
        f"RISK: {risk_result[:100]}. "
        f"FRAUD: {fraud_result[:100]}."
    )


def parse_decision(result: str) -> str:
    """
    Parse the LLM result to determine final status.
    
    Args:
        result: Raw LLM response
        
    Returns:
        Final status: 'approved', 'conditional', or 'declined'
    """
    result_upper = result.upper()
    if "APPROVED" in result_upper and "CONDITIONAL" not in result_upper:
        return "approved"
    elif "CONDITIONAL" in result_upper:
        return "conditional"
    else:
        return "declined"
