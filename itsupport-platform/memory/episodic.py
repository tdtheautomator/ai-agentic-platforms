"""
Episodic memory — SQLite audit log for tickets.

Stores all events and ticket state for audit trail and recovery.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

# Module-level state
_sqlite_path: Path = None


def _db() -> sqlite3.Connection:
    """Get SQLite connection."""
    c = sqlite3.connect(str(_sqlite_path))
    c.row_factory = sqlite3.Row
    return c


def _init_db(sqlite_path: Path) -> None:
    """Initialize SQLite schema."""
    global _sqlite_path
    _sqlite_path = sqlite_path
    
    with _db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS ticket_events (
            id TEXT PRIMARY KEY, ticket_id TEXT, session_num INTEGER,
            agent TEXT, event TEXT, detail TEXT, outcome TEXT, ts TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY, reporter TEXT, device TEXT, category TEXT,
            priority TEXT, description TEXT, status TEXT,
            os_version TEXT, created_at TEXT, updated_at TEXT)""")
        c.commit()


def epi_log(ticket_id: str, session: int, agent: str,
            event: str, detail: str, outcome: str = "") -> None:
    """Log event to audit trail."""
    with _db() as c:
        c.execute("INSERT INTO ticket_events VALUES (?,?,?,?,?,?,?,?)",
                  (str(uuid.uuid4())[:8], ticket_id, session, agent,
                   event, detail, outcome,
                   datetime.utcnow().isoformat(timespec="seconds")))
        c.commit()


def epi_list(ticket_id: str) -> list[dict]:
    """Retrieve all events for a ticket."""
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM ticket_events WHERE ticket_id=? ORDER BY ts",
            (ticket_id,)).fetchall()
    return [dict(r) for r in rows]


def ticket_upsert(t: dict) -> None:
    """Insert or update ticket."""
    with _db() as c:
        c.execute("""INSERT OR REPLACE INTO tickets
            VALUES (:id,:reporter,:device,:category,:priority,:description,
                    :status,:os_version,:created_at,:updated_at)""", t)
        c.commit()


def ticket_list(limit: int = 15) -> list[dict]:
    """List recent tickets."""
    with _db() as c:
        rows = c.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?",
            (limit,)).fetchall()
    return [dict(r) for r in rows]
