import os
import sqlite3
from typing import Generator
from contextlib import contextmanager
from app.core.config import settings

# SQLite DB Path (LOCAL_DEMO persistent operational store only)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "finrecon_local.db")

def get_db_path() -> str:
    return os.environ.get("FINRECON_DB_PATH") or DB_PATH

def get_db_connection() -> sqlite3.Connection:
    path = get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


@contextmanager
def get_db_context() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections, guaranteeing connection closure and rollback on errors.
    """
    conn = get_db_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """
    LOCAL_DEMO Operational SQLite Persistence Initialization.
    Note: SQLite is strictly an embedded persistent store for LOCAL_DEMO mode.
    It is NOT an enterprise production database.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: Exceptions (Financial fields read-only, triage fields mutable)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exceptions (
        exception_id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        transaction_id TEXT NOT NULL,
        reason_code TEXT NOT NULL,
        reason_description TEXT NOT NULL,
        severity TEXT NOT NULL,
        reconciliation_status TEXT NOT NULL,
        bank_amount REAL NOT NULL,
        merchant_amount REAL NOT NULL,
        amount_difference REAL NOT NULL,
        bank_status TEXT NOT NULL,
        merchant_status TEXT NOT NULL,
        triage_status TEXT NOT NULL,
        assigned_to TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        resolved_at TEXT,
        resolution_code TEXT,
        resolution_notes TEXT
    );
    """)

    # Table 2: Investigation Notes (Append-Only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investigation_notes (
        note_id TEXT PRIMARY KEY,
        exception_id TEXT NOT NULL,
        author TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        note_text TEXT NOT NULL,
        FOREIGN KEY(exception_id) REFERENCES exceptions(exception_id)
    );
    """)

    # Table 3: Operational Audit Events (Append-Only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_events (
        event_id TEXT PRIMARY KEY,
        exception_id TEXT NOT NULL,
        batch_id TEXT NOT NULL,
        actor TEXT NOT NULL,
        role TEXT NOT NULL,
        event_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        old_status TEXT,
        new_status TEXT,
        details TEXT NOT NULL
    );
    """)

    # Table 4: Batch Control Checkpoints (Feature A: Self-Healing Control)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batch_control_checkpoints (
        id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        input_record_count INTEGER NOT NULL,
        output_record_count INTEGER NOT NULL,
        input_amount_total REAL NOT NULL,
        output_amount_total REAL NOT NULL,
        duplicate_count INTEGER DEFAULT 0,
        matched_count INTEGER DEFAULT 0,
        mismatch_count INTEGER DEFAULT 0,
        missing_count INTEGER DEFAULT 0,
        return_code INTEGER DEFAULT 0,
        control_status TEXT NOT NULL,
        checksum TEXT,
        lineage_ref TEXT,
        recovery_status TEXT NOT NULL,
        recovery_attempt INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        error_reason TEXT
    );
    """)

    # Table 5: Recovery Events (Feature A: Batch Recovery Audit Log)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recovery_events (
        id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        event_type TEXT NOT NULL,
        attempt_number INTEGER NOT NULL,
        status TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Table 6: Transaction Lineage (Feature B: Provenance Graph)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transaction_lineage (
        id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        transaction_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        stage_name TEXT NOT NULL,
        source_system TEXT NOT NULL,
        record_reference TEXT,
        reason_code TEXT,
        previous_state TEXT,
        new_state TEXT,
        actor TEXT NOT NULL,
        actor_role TEXT NOT NULL,
        metadata_json TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # Table 7: Intelligent Match Results (Feature C: Explainable AI Match)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS intelligent_match_results (
        id TEXT PRIMARY KEY,
        batch_id TEXT NOT NULL,
        bank_transaction_id TEXT NOT NULL,
        candidate_transaction_id TEXT NOT NULL,
        confidence_score REAL NOT NULL,
        decision TEXT NOT NULL,
        confidence_classification TEXT NOT NULL,
        feature_scores_json TEXT NOT NULL,
        model_version TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # Table 8: User Accounts (Phase 8 Secure Authentication & RBAC)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT,
        is_active INTEGER DEFAULT 1,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Table 9: User Sessions (Session Token Storage)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    conn.commit()
    conn.close()

