"""Episodic memory management (SQLite)."""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class EpisodicMemory:
    """Episodic memory backed by SQLite."""

    def __init__(self, db_path: Path):
        """
        Initialize episodic memory.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        c = sqlite3.connect(str(self.db_path))
        c.row_factory = sqlite3.Row
        return c

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._get_connection() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS order_events (
                id TEXT PRIMARY KEY, order_id TEXT, session_num INTEGER,
                agent TEXT, event TEXT, detail TEXT, outcome TEXT, ts TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY, customer_id TEXT, customer_name TEXT,
                items TEXT, subtotal REAL, discount REAL, shipping REAL,
                total REAL, status TEXT, warehouse TEXT,
                created_at TEXT, updated_at TEXT)""")
            c.commit()

    def log_event(
        self,
        order_id: str,
        session: int,
        agent: str,
        event: str,
        detail: str,
        outcome: str = "",
    ) -> None:
        """
        Log an event.
        
        Args:
            order_id: Order ID
            session: Session number
            agent: Agent name
            event: Event type
            detail: Event detail
            outcome: Event outcome
        """
        with self._get_connection() as c:
            c.execute(
                "INSERT INTO order_events VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4())[:8],
                    order_id,
                    session,
                    agent,
                    event,
                    detail,
                    outcome,
                    datetime.utcnow().isoformat(timespec="seconds"),
                ),
            )
            c.commit()

    def upsert_order(self, order: dict) -> None:
        """
        Upsert an order.
        
        Args:
            order: Order data
        """
        with self._get_connection() as c:
            c.execute(
                """INSERT OR REPLACE INTO orders
                VALUES (:id,:customer_id,:customer_name,:items,:subtotal,:discount,
                        :shipping,:total,:status,:warehouse,:created_at,:updated_at)""",
                order,
            )
            c.commit()

    def get_orders(self, limit: int = 15) -> list[dict]:
        """
        Get recent orders.
        
        Args:
            limit: Number of orders to return
            
        Returns:
            List of orders
        """
        with self._get_connection() as c:
            rows = c.execute(
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_events(self, order_id: str) -> list[dict]:
        """
        Get events for an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            List of events
        """
        with self._get_connection() as c:
            rows = c.execute(
                "SELECT * FROM order_events WHERE order_id=? ORDER BY ts",
                (order_id,),
            ).fetchall()
        return [dict(r) for r in rows]
