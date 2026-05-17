"""
SDK Tool registry and implementations for IT Support demo.

Tools for user profile, system health, knowledge base search, SLA check, and pattern detection.
"""

from datetime import datetime

from memory import sem_query
from data import DIAG_RESULTS, KB_ARTICLES, USERS

# Tool registry
TOOLS: dict[str, dict] = {}


def tool(fn):
    """Decorator to register tool with schema."""
    TOOLS[fn.__name__] = {
        "name": fn.__name__,
        "description": fn.__doc__ or "",
        "params": list(fn.__code__.co_varnames[:fn.__code__.co_argcount]),
        "fn": fn,
    }
    return fn


@tool
def get_user_profile(user_id: str) -> dict:
    """Retrieve user profile including device, OS, and support tier."""
    u = next((x for x in USERS if x["id"] == user_id), None)
    return u or {"error": "User not found"}


@tool
def check_system_health(user_id: str, category: str) -> dict:
    """Run automated system health diagnostics for the reported issue category."""
    u = next((x for x in USERS if x["id"] == user_id), None)
    if not u:
        return {"error": "User not found"}
    data = DIAG_RESULTS.get(category, {"status": "unknown"})
    return {
        "user_id": user_id,
        "device": u["device"],
        "os": u["os"],
        "category": category,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        **data,
    }


@tool
def search_knowledge_base(query: str) -> list[str]:
    """Search the IT knowledge base for relevant resolution articles."""
    results = sem_query(query, top_k=2)
    if not results:
        kw = query.lower()
        results = [a for a in KB_ARTICLES
                   if any(w in a.lower() for w in kw.split())][:2]
    return results or ["No matching article found — escalate to L2 support."]


@tool
def check_sla_status(priority: str, created_at: str) -> dict:
    """Check if the ticket is within SLA thresholds based on priority."""
    sla_hours = {"CRITICAL": 1, "HIGH": 4, "MEDIUM": 8, "LOW": 24}.get(priority, 8)
    elapsed = (datetime.utcnow() - datetime.fromisoformat(created_at)).total_seconds() / 3600
    remaining = max(0, sla_hours - elapsed)
    return {
        "priority": priority,
        "sla_hours": sla_hours,
        "elapsed_hours": round(elapsed, 2),
        "remaining_hours": round(remaining, 2),
        "sla_breached": elapsed > sla_hours,
        "sla_warning": remaining < sla_hours * 0.25,
    }


@tool
def check_similar_tickets(category: str) -> dict:
    """Check for similar recent tickets to identify pattern or outage."""
    # Deterministic dummy counts per category
    counts = {
        "Network / VPN": {"similar_24h": 12, "pattern_detected": True, "potential_outage": True, "affected_users": 18},
        "Software / Application": {"similar_24h": 4, "pattern_detected": True, "potential_outage": False, "affected_users": 4},
        "Account / Access": {"similar_24h": 1, "pattern_detected": False, "potential_outage": False, "affected_users": 1},
        "Hardware / Peripherals": {"similar_24h": 2, "pattern_detected": False, "potential_outage": False, "affected_users": 2},
        "Performance / Crash": {"similar_24h": 3, "pattern_detected": True, "potential_outage": False, "affected_users": 3},
        "Email / Calendar": {"similar_24h": 8, "pattern_detected": True, "potential_outage": False, "affected_users": 8},
        "Security / Malware": {"similar_24h": 1, "pattern_detected": False, "potential_outage": False, "affected_users": 1},
    }
    data = counts.get(category, {"similar_24h": 0, "pattern_detected": False, "potential_outage": False, "affected_users": 0})
    return {
        "category": category,
        **data,
        "recommendation": "Investigate potential service outage" if data["potential_outage"]
        else "Standard individual resolution"
    }
