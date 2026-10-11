import pytest
import sys
import os
import io

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from fastapi.testclient import TestClient
from app.main import app
from app.repositories.exception_repository import exception_repo
from app.repositories.audit_repository import audit_repo
from app.db.database import init_db, DB_PATH, get_db_connection

client = TestClient(app)

def setup_function():
    # Ensure fresh DB state
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investigation_notes")
    cursor.execute("DELETE FROM audit_events")
    cursor.execute("DELETE FROM exceptions")
    conn.commit()
    conn.close()
    exception_repo._ensure_seeded()

def test_tc_p5_01_sqlite_initialization():
    assert os.path.exists(DB_PATH)
    exc_summary = exception_repo.get_summary()
    assert exc_summary.total_exceptions == 30

def test_tc_p5_02_exception_persistence():
    exc = exception_repo.get_by_id("EXC-10031")
    assert exc is not None
    assert exc.transaction_id == "TXN10031"
    assert exc.bank_amount == 1250.50

def test_tc_p5_03_note_persistence():
    note = exception_repo.add_note("EXC-10031", author="ANALYST_01", note_text="SQLite note persistence test")
    assert note.note_id is not None
    
    exc = exception_repo.get_by_id("EXC-10031")
    assert any(n.note_text == "SQLite note persistence test" for n in exc.notes)

def test_tc_p5_04_audit_persistence():
    ev = audit_repo.log_event(
        exception_id="EXC-10031",
        batch_id="FINREC-20260922-001",
        event_type="NOTE_ADDED",
        actor="ANALYST_01",
        role="ANALYST",
        details="Audit persistence test event"
    )
    assert ev.event_id.startswith("AUD-")
    all_events = audit_repo.get_events_for_exception("EXC-10031")
    assert any(e.event_id == ev.event_id for e in all_events)

def test_tc_p5_05_application_restart_preserves_triage_data():
    """
    EXPLICIT PERSISTENCE RESTART TEST (Requirement 10):
    Create/modify triage data -> Reset repository connection -> Retrieve exception -> Verify all triage data & audit events intact.
    """
    exc_id = "EXC-10035"
    
    # 1. Assign (automatically transitions UNASSIGNED -> IN_REVIEW)
    exception_repo.assign(exc_id, assignee="ANALYST_02", actor="SUPERVISOR_01", role="SUPERVISOR")
    
    # 2. Add Note
    exception_repo.add_note(exc_id, author="ANALYST_02", note_text="App restart test note", role="ANALYST")
    
    # 3. Simulate Complete Backend Service Restart by re-instantiating fresh repositories
    from app.repositories.exception_repository import ExceptionRepository
    from app.repositories.audit_repository import AuditRepository
    
    fresh_exc_repo = ExceptionRepository()
    fresh_audit_repo = AuditRepository()
    
    # 4. Retrieve Same Exception from SQLite
    restarted_exc = fresh_exc_repo.get_by_id(exc_id)
    assert restarted_exc is not None
    assert restarted_exc.assigned_to == "ANALYST_02"
    assert restarted_exc.triage_status.value == "IN_REVIEW"
    assert any(n.note_text == "App restart test note" for n in restarted_exc.notes)
    
    # 5. Verify Audit Events Intact
    restarted_audit = fresh_audit_repo.get_events_for_exception(exc_id)
    assert any(e.event_type == "EXCEPTION_ASSIGNED" for e in restarted_audit)
    assert any(e.event_type == "NOTE_ADDED" for e in restarted_audit)

def test_tc_p5_06_analyst_permission_enforcement():
    # Analyst can assign and add note
    headers = {"X-User-Name": "ANALYST_01", "X-User-Role": "ANALYST"}
    res_assign = client.post("/api/v1/exceptions/EXC-10032/assign", json={"assignee": "ANALYST_01"}, headers=headers)
    assert res_assign.status_code == 200

    res_note = client.post("/api/v1/exceptions/EXC-10032/notes", json={"note_text": "Analyst note"}, headers=headers)
    assert res_note.status_code == 200

def test_tc_p5_07_supervisor_permission_enforcement():
    # Supervisor can resolve case (Assign first so status is IN_REVIEW)
    exception_repo.assign("EXC-10032", assignee="ANALYST_01")
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.post(
        "/api/v1/exceptions/EXC-10032/status",
        json={
            "target_status": "RESOLVED",
            "resolution_code": "RESOLVED_VALID_TRANSACTION",
            "resolution_notes": "Supervisor approved resolution"
        },
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["triage_status"] == "RESOLVED"

def test_tc_p5_08_unauthorized_operation_returns_403():
    # Analyst attempting to RESOLVE case must be rejected with 403 Forbidden!
    analyst_headers = {"X-User-Name": "ANALYST_01", "X-User-Role": "ANALYST"}
    res_status = client.post(
        "/api/v1/exceptions/EXC-10033/status",
        json={
            "target_status": "RESOLVED",
            "resolution_code": "RESOLVED_VALID_TRANSACTION",
            "resolution_notes": "Unauthorized attempt"
        },
        headers=analyst_headers
    )
    assert res_status.status_code == 403
    assert "requires SUPERVISOR role" in res_status.json()["detail"]

    # Analyst attempting to download Excel export must be rejected with 403 Forbidden!
    res_export = client.get("/api/v1/reports/reconciliation.xlsx", headers=analyst_headers)
    assert res_export.status_code == 403

def test_tc_p5_09_invalid_input_validation():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    # Empty assignee
    res1 = client.post("/api/v1/exceptions/EXC-10031/assign", json={"assignee": "  "}, headers=headers)
    assert res1.status_code == 400

    # Negative skip
    res2 = client.get("/api/v1/exceptions?skip=-1", headers=headers)
    assert res2.status_code == 422 # Pydantic validation error

def test_tc_p5_10_security_headers():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in res.headers
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

def test_tc_p5_11_cors_configuration():
    res = client.options("/api/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers

def test_tc_p5_12_exception_csv_export():
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.get("/api/v1/reports/exceptions.csv", headers=sup_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    content = res.text
    assert "Exception ID" in content
    assert "TXN10031" in content

def test_tc_p5_13_audit_csv_export():
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.get("/api/v1/reports/audit.csv", headers=sup_headers)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    content = res.text
    assert "Event ID" in content
    assert "Actor" in content

def test_tc_p5_14_excel_export():
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.get("/api/v1/reports/reconciliation.xlsx", headers=sup_headers)
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers["content-type"]
    assert len(res.content) > 500

def test_tc_p5_15_pdf_export():
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.get("/api/v1/reports/reconciliation.pdf", headers=sup_headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

def test_tc_p5_16_report_exported_audit_event():
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    client.get("/api/v1/reports/exceptions.csv", headers=sup_headers)
    
    events = audit_repo.get_all_events(event_type="REPORT_EXPORTED")
    assert len(events) > 0
    assert events[0].actor == "SUPERVISOR_01"

def test_tc_p5_17_advanced_exception_filtering():
    res = client.get("/api/v1/exceptions?severity=CRITICAL&reason_code=RCN-104")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    assert all(e["severity"] == "CRITICAL" and e["reason_code"] == "RCN-104" for e in data)

def test_tc_p5_18_advanced_audit_filtering():
    events = audit_repo.get_all_events(role="SUPERVISOR")
    assert all(e.role == "SUPERVISOR" for e in events)

def test_tc_p5_19_pagination():
    res = client.get("/api/v1/exceptions?skip=5&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10

def test_tc_p5_20_financial_fields_immutability():
    exc_before = client.get("/api/v1/exceptions/EXC-10031").json()
    
    # Perform triage actions
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    client.post("/api/v1/exceptions/EXC-10031/assign", json={"assignee": "ANALYST_01"}, headers=headers)
    client.post("/api/v1/exceptions/EXC-10031/notes", json={"note_text": "Immutability check note"}, headers=headers)
    
    exc_after = client.get("/api/v1/exceptions/EXC-10031").json()
    
    # STRICT ASSERTION: Read-only financial fields MUST NOT CHANGE
    assert exc_after["bank_amount"] == exc_before["bank_amount"]
    assert exc_after["merchant_amount"] == exc_before["merchant_amount"]
    assert exc_after["amount_difference"] == exc_before["amount_difference"]
    assert exc_after["reason_code"] == exc_before["reason_code"]

def test_tc_p5_21_local_demo_identity_display():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["mode"] == "LOCAL_DEMO"

def test_tc_p5_22_real_mainframe_unconfigured():
    from app.adapters.real_mainframe import RealMainframeAdapter
    adapter = RealMainframeAdapter()
    assert adapter.mode.value == "REAL_MAINFRAME"
    with pytest.raises(NotImplementedError):
        adapter.submit_batch("FINREC-001")
