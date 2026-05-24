"""
Query Banking Rules Tool

Searches the regulatory knowledge base for relevant banking and compliance rules.
"""

from tools.registry import register_tool


# Import BANKING_RULES and sem_query from main module (will be injected at runtime)
def _get_banking_rules():
    """Get banking rules list from main module."""
    from main import BANKING_RULES
    return BANKING_RULES


def _get_sem_query():
    """Get semantic query function from main module."""
    from main import sem_query
    return sem_query


@register_tool
def query_banking_rules(topic: str) -> list[str]:
    """Search the regulatory knowledge base for relevant rules."""
    sem_query = _get_sem_query()
    banking_rules = _get_banking_rules()
    
    results = sem_query(topic, top_k=2)
    if not results:
        # fallback keyword match
        kw = topic.lower()
        results = [r for r in banking_rules
                   if any(w in r.lower() for w in kw.split())][:2]
    return results or ["No specific rule found — apply standard lending criteria."]
