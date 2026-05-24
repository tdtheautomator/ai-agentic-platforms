"""
Fraud Agent Prompts

System prompts and message templates for the fraud detection agent.
"""

SYSTEM_PROMPT = (
    "You are a fraud analyst at a retail bank. "
    "Given transaction data and fraud flags, write a 2-sentence fraud assessment. "
    "State whether the application should proceed, be flagged for review, or be blocked. "
    "Reference specific signals. Be direct."
)


def build_user_message(
    customer: dict,
    fraud_flags: bool,
    declined_30d: int,
    foreign_tx: int,
    cached_risk: str | None = None,
) -> str:
    """
    Build the user message for the fraud agent.
    
    Args:
        customer: Customer profile dictionary
        fraud_flags: Whether fraud flags are present
        declined_30d: Number of declined transactions in last 30 days
        foreign_tx: Number of foreign transactions
        cached_risk: Upstream risk level from working memory
        
    Returns:
        Formatted user message for the LLM
    """
    return (
        f"Transaction history (30 days): {customer['tx_count']} total, "
        f"{declined_30d} declined, {foreign_tx} foreign. "
        f"Fraud flags: {fraud_flags}. "
        f"Specific signals: none. "
        f"Upstream risk level: {cached_risk or 'MEDIUM'}."
    )
