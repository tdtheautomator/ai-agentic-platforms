"""
Episodic memory store for banking-demo using SQLite.

Stores audit trail events (loan applications, agent decisions, etc.)
in SQLite with Alembic-managed schema. Implements the MemoryStore interface.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from memory.base import MemoryStore

logger = structlog.get_logger(__name__)


class EpisodicMemory(MemoryStore):
    """
    Episodic memory using SQLite.
    
    Stores audit trail events for loan applications and agent decisions.
    Provides query capabilities for retrieving events by application ID.
    
    Attributes:
        db_path: Path to SQLite database file.
    """

    def __init__(self, db_path: str | Path = "/data/sqlite/banking.db"):
        """
        Initialize episodic memory.
        
        Args:
            db_path: Path to SQLite database (default: /data/sqlite/banking.db).
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def store_name(self) -> str:
        """Get store name."""
        return "episodic"

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection with row factory.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    async def add(
        self,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an event to the episodic audit trail.
        
        Args:
            key: Application ID.
            value: Event details (dict with agent, event, detail, outcome).
            metadata: Optional metadata (ignored).
        """
        if not isinstance(value, dict):
            value = {"event": str(value)}

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO loan_events 
                   (id, application_id, session_num, agent, event, detail, outcome, ts)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    key[:8],  # id
                    value.get("app_id", key),  # application_id
                    value.get("session_num", 0),  # session_num
                    value.get("agent", "unknown"),  # agent
                    value.get("event", ""),  # event
                    value.get("detail", ""),  # detail
                    value.get("outcome", ""),  # outcome
                    datetime.utcnow().isoformat(timespec="seconds"),  # ts
                ),
            )

            conn.commit()
            conn.close()

            await logger.ainfo(
                "episodic_memory_add",
                app_id=value.get("app_id", key),
                event=value.get("event", ""),
            )

        except Exception as exc:
            await logger.aerror(
                "episodic_memory_add_failed",
                error=str(exc),
            )
            raise

    async def get(self, key: str) -> Any | None:
        """
        Get the first event for an application.
        
        Args:
            key: Application ID.
            
        Returns:
            First event dict, or None if not found.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM loan_events WHERE application_id=? LIMIT 1",
                (key,),
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as exc:
            await logger.aerror(
                "episodic_memory_get_failed",
                error=str(exc),
            )
            raise

    async def search(
        self,
        query: str,
        top_k: int = 2,
    ) -> list[Any]:
        """
        Search events by application ID.
        
        Args:
            query: Application ID to search for.
            top_k: Maximum number of results.
            
        Returns:
            List of matching event dicts.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM loan_events WHERE application_id=? ORDER BY ts DESC LIMIT ?",
                (query, top_k),
            )
            rows = cursor.fetchall()
            conn.close()

            return [dict(r) for r in rows]

        except Exception as exc:
            await logger.aerror(
                "episodic_memory_search_failed",
                error=str(exc),
            )
            raise

    async def clear(self) -> None:
        """Clear all events from episodic memory."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM loan_events")
            conn.commit()
            conn.close()

            await logger.ainfo("episodic_memory_cleared")

        except Exception as exc:
            await logger.aerror(
                "episodic_memory_clear_failed",
                error=str(exc),
            )
            raise

    async def count(self) -> int:
        """Get the number of events in episodic memory."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM loan_events")
            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as exc:
            await logger.aerror(
                "episodic_memory_count_failed",
                error=str(exc),
            )
            return 0

    async def get_all(self, app_id: str) -> list[dict[str, Any]]:
        """
        Get all events for an application.
        
        Args:
            app_id: Application ID.
            
        Returns:
            List of all event dicts for the application.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM loan_events WHERE application_id=? ORDER BY ts",
                (app_id,),
            )
            rows = cursor.fetchall()
            conn.close()

            return [dict(r) for r in rows]

        except Exception as exc:
            await logger.aerror(
                "episodic_memory_get_all_failed",
                error=str(exc),
            )
            raise
