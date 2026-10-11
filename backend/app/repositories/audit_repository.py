import datetime
import uuid
import sqlite3
from typing import List, Optional
from app.models.schemas import AuditEventModel
from app.db.database import get_db_connection, init_db

class AuditRepository:
    """
    SQLite Persistent Audit Trail Repository for LOCAL_DEMO mode.
    Guarantees immutability and complete event tracking across app restarts.
    """
    def __init__(self):
        init_db()

    def log_event(
        self,
        exception_id: str,
        batch_id: str,
        event_type: str,
        actor: str,
        details: str,
        role: str = "ANALYST",
        old_status: Optional[str] = None,
        new_status: Optional[str] = None
    ) -> AuditEventModel:
        event = AuditEventModel(
            event_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            exception_id=exception_id,
            batch_id=batch_id,
            actor=actor,
            role=role,
            event_type=event_type,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            old_status=old_status,
            new_status=new_status,
            details=details
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_events (event_id, exception_id, batch_id, actor, role, event_type, timestamp, old_status, new_status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id, event.exception_id, event.batch_id, event.actor, event.role,
            event.event_type, event.timestamp, event.old_status, event.new_status, event.details
        ))
        conn.commit()
        conn.close()
        return event

    def get_events_for_exception(self, exception_id: str) -> List[AuditEventModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_events WHERE exception_id = ? ORDER BY timestamp ASC", (exception_id,))
        rows = cursor.fetchall()
        conn.close()
        return [
            AuditEventModel(
                event_id=row["event_id"],
                exception_id=row["exception_id"],
                batch_id=row["batch_id"],
                actor=row["actor"],
                role=row["role"],
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                old_status=row["old_status"],
                new_status=row["new_status"],
                details=row["details"]
            ) for row in rows
        ]

    def get_all_events(
        self,
        batch_id: Optional[str] = None,
        exception_id: Optional[str] = None,
        actor: Optional[str] = None,
        role: Optional[str] = None,
        event_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 500
    ) -> List[AuditEventModel]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        if batch_id:
            query += " AND batch_id = ?"
            params.append(batch_id)
        if exception_id:
            query += " AND exception_id = ?"
            params.append(exception_id)
        if actor:
            query += " AND UPPER(actor) = ?"
            params.append(actor.upper())
        if role:
            query += " AND UPPER(role) = ?"
            params.append(role.upper())
        if event_type:
            query += " AND UPPER(event_type) = ?"
            params.append(event_type.upper())

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()

        return [
            AuditEventModel(
                event_id=row["event_id"],
                exception_id=row["exception_id"],
                batch_id=row["batch_id"],
                actor=row["actor"],
                role=row["role"],
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                old_status=row["old_status"],
                new_status=row["new_status"],
                details=row["details"]
            ) for row in rows
        ]

audit_repo = AuditRepository()
