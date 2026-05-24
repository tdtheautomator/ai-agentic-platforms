"""
Session state management for banking-demo.

Tracks harness session state, progress, and results across
multiple stages of the loan pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SessionState:
    """
    Harness session state.
    
    Tracks progress, results, and metadata for a loan application
    across all pipeline stages.
    
    Attributes:
        app_id: Unique application ID.
        session_num: Current session number (1–5).
        customer: Customer profile.
        loan: Loan details.
        progress: Dict of agent progress (pending, running, complete).
        results: Dict of agent results.
        context_size: Current context memory size.
        compactions: Number of context compactions performed.
        created_at: Session creation timestamp.
        updated_at: Last update timestamp.
    """

    app_id: str
    session_num: int
    customer: dict[str, Any]
    loan: dict[str, Any]
    progress: dict[str, str] = field(default_factory=dict)
    results: dict[str, str] = field(default_factory=dict)
    context_size: int = 0
    compactions: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        """Initialize timestamps."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

    def set_agent_progress(self, agent: str, status: str) -> None:
        """
        Update agent progress.
        
        Args:
            agent: Agent name.
            status: Progress status (pending, running, complete, error).
        """
        self.progress[agent] = status
        self.updated_at = datetime.utcnow().isoformat()

    def set_agent_result(self, agent: str, result: str) -> None:
        """
        Store agent result.
        
        Args:
            agent: Agent name.
            result: Result text from agent.
        """
        self.results[agent] = result
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert session to dictionary.
        
        Returns:
            Dictionary representation of session state.
        """
        return {
            "app_id": self.app_id,
            "session_num": self.session_num,
            "customer": self.customer,
            "loan": self.loan,
            "progress": self.progress,
            "results": self.results,
            "context_size": self.context_size,
            "compactions": self.compactions,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
