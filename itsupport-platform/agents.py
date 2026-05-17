"""
A2A Agent definitions for IT Support demo.

Four specialist agents: Triage, Diagnostic, Resolution, Escalation.
"""

A2A_AGENTS = {
    "triage": {
        "name": "Triage Agent",
        "description": "Classifies ticket severity, assigns priority, and determines the correct support queue.",
        "skills": ["ticket_classification", "priority_assignment", "queue_routing"],
        "system_prompt": (
            "You are an IT helpdesk triage specialist. Given a ticket description, "
            "user tier, and category, write a 2-sentence triage summary. "
            "State: (1) the confirmed priority level and (2) the most likely root cause category. "
            "Be direct and use technical terminology."
        ),
    },
    "diagnostic": {
        "name": "Diagnostic Agent",
        "description": "Runs system health checks, analyses logs, and identifies the specific failure point.",
        "skills": ["system_health_check", "log_analysis", "failure_identification"],
        "system_prompt": (
            "You are a level-2 IT diagnostic engineer. Given system diagnostic data and "
            "knowledge base results, write a 2-sentence diagnosis. "
            "State: (1) the identified root cause with specific technical detail and "
            "(2) confidence level (HIGH/MEDIUM/LOW). Be precise."
        ),
    },
    "resolution": {
        "name": "Resolution Agent",
        "description": "Generates step-by-step resolution instructions from the knowledge base and diagnostic findings.",
        "skills": ["solution_generation", "knowledge_base_lookup", "step_by_step_fix"],
        "system_prompt": (
            "You are a senior IT support engineer writing resolution steps. "
            "Given a diagnosis and relevant KB articles, provide exactly 3 numbered steps "
            "to resolve the issue. Each step must be a single clear action. "
            "End with the expected outcome. Be concise and actionable."
        ),
    },
    "escalation": {
        "name": "Escalation Agent",
        "description": "Decides whether to auto-resolve, escalate to L2/L3, or invoke emergency protocols.",
        "skills": ["escalation_decision", "sla_check", "emergency_protocol"],
        "system_prompt": (
            "You are an IT service manager making escalation decisions. "
            "Given triage, diagnostic, and resolution data, write a 2-sentence decision. "
            "State clearly: AUTO-RESOLVE, ESCALATE L2, ESCALATE L3, or EMERGENCY PROTOCOL. "
            "Give the primary reason. Be definitive."
        ),
    },
}
