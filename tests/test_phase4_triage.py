import pytest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from fastapi.testclient import TestClient
from app.main import app
from app.repositories.exception_repository import exception_repo
from app.db.database import get_db_connection, init_db

client = TestClient(app)

def setup_function():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investigation_notes")
    cursor.execute("DELETE FROM audit_events")
    cursor.execute("DELETE FROM exceptions")
    conn.commit()
    conn.close()
    exception_repo._ensure_seeded()

def test_tc_p4_01_list_exceptions():
    res = client.get("/api/v1/exceptions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 30
    assert "exception_id" in data[0]

def test_tc_p4_02_filter_by_severity():
    res = client.get("/api/v1/exceptions?severity=CRITICAL")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 20
    assert all(e["severity"] == "CRITICAL" for e in data)

    res_high = client.get("/api/v1/exceptions?severity=HIGH")
    assert res_high.status_code == 200
    assert len(res_high.json()) == 10

def test_tc_p4_03_filter_by_reason_code():
    res = client.get("/api/v1/exceptions?reason_code=RCN-101")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 5
    assert all(e["reason_code"] == "RCN-101" for e in data)

def test_tc_p4_04_filter_by_triage_status():
    res = client.get("/api/v1/exceptions?triage_status=UNASSIGNED")
    assert res.status_code == 200
    assert len(res.json()) == 30

def test_tc_p4_05_search_by_transaction_id():
    res = client.get("/api/v1/exceptions?trxn_id=TXN10031")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["transaction_id"] == "TXN10031"

def test_tc_p4_06_assign_exception():
    res = client.post("/api/v1/exceptions/EXC-10031/assign", json={"assignee": "analyst01", "actor": "SUPERVISOR"})
    assert res.status_code == 200
    data = res.json()
    assert data["assigned_to"] == "analyst01"
    # Auto transitions UNASSIGNED -> IN_REVIEW
    assert data["triage_status"] == "IN_REVIEW"

def test_tc_p4_07_reject_empty_assignee():
    res = client.post("/api/v1/exceptions/EXC-10031/assign", json={"assignee": "   "})
    assert res.status_code == 400
    assert "Assignee cannot be empty" in res.json()["detail"]

def test_tc_p4_08_move_unassigned_to_in_review():
    res = client.post("/api/v1/exceptions/EXC-10032/status", json={"target_status": "IN_REVIEW"})
    assert res.status_code == 200
    assert res.json()["triage_status"] == "IN_REVIEW"

def test_tc_p4_09_reject_invalid_status_transition():
    # UNASSIGNED -> RESOLVED directly is invalid
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.post(
        "/api/v1/exceptions/EXC-10033/status",
        json={
            "target_status": "RESOLVED",
            "resolution_code": "RESOLVED_VALID_TRANSACTION",
            "resolution_notes": "Attempting direct resolve"
        },
        headers=sup_headers
    )
    assert res.status_code == 400
    assert "Invalid state transition" in res.json()["detail"]

def test_tc_p4_10_add_investigation_note():
    res = client.post(
        "/api/v1/exceptions/EXC-10031/notes",
        json={"author": "analyst01", "note_text": "Merchant feed posted transaction 1 day later"}
    )
    assert res.status_code == 200
    note = res.json()
    assert note["note_text"] == "Merchant feed posted transaction 1 day later"
    assert note["author"] == "analyst01"

    # Verify note persisted on exception
    exc = client.get("/api/v1/exceptions/EXC-10031").json()
    assert len(exc["notes"]) == 1
    assert exc["notes"][0]["note_text"] == "Merchant feed posted transaction 1 day later"

def test_tc_p4_11_reject_empty_note():
    res = client.post("/api/v1/exceptions/EXC-10031/notes", json={"author": "analyst01", "note_text": "  "})
    assert res.status_code == 400
    assert "Note text cannot be empty" in res.json()["detail"]

def test_tc_p4_12_resolve_exception_with_valid_resolution():
    # 1. Move UNASSIGNED -> IN_REVIEW
    client.post("/api/v1/exceptions/EXC-10031/status", json={"target_status": "IN_REVIEW"})

    # 2. Move IN_REVIEW -> RESOLVED with valid resolution
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.post(
        "/api/v1/exceptions/EXC-10031/status",
        json={
            "target_status": "RESOLVED",
            "resolution_code": "RESOLVED_SOURCE_DELAY",
            "resolution_notes": "Verified source delay from merchant gateway log"
        },
        headers=sup_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triage_status"] == "RESOLVED"
    assert data["resolution_code"] == "RESOLVED_SOURCE_DELAY"
    assert data["resolution_notes"] == "Verified source delay from merchant gateway log"
    assert data["resolved_at"] is not None

def test_tc_p4_13_reject_resolution_without_required_data():
    client.post("/api/v1/exceptions/EXC-10031/status", json={"target_status": "IN_REVIEW"})
    
    # Missing resolution notes
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.post(
        "/api/v1/exceptions/EXC-10031/status",
        json={
            "target_status": "RESOLVED",
            "resolution_code": "RESOLVED_VALID_TRANSACTION",
            "resolution_notes": ""
        },
        headers=sup_headers
    )
    assert res.status_code == 400
    assert "Resolution notes are required" in res.json()["detail"]

def test_tc_p4_14_reject_exception_with_valid_rejection_data():
    client.post("/api/v1/exceptions/EXC-10034/status", json={"target_status": "IN_REVIEW"})
    sup_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    res = client.post(
        "/api/v1/exceptions/EXC-10034/status",
        json={
            "target_status": "REJECTED",
            "resolution_code": "REJECTED_FALSE_POSITIVE",
            "resolution_notes": "Determined to be system false positive after log analysis"
        },
        headers=sup_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["triage_status"] == "REJECTED"
    assert data["resolution_code"] == "REJECTED_FALSE_POSITIVE"

def test_tc_p4_15_verify_audit_event_created():
    client.post("/api/v1/exceptions/EXC-10031/assign", json={"assignee": "analyst01"})
    res = client.get("/api/v1/exceptions/EXC-10031/audit")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 2 # EXCEPTION_CREATED + EXCEPTION_ASSIGNED
    assert any(e["event_type"] == "EXCEPTION_ASSIGNED" for e in events)

def test_tc_p4_16_verify_financial_fields_remain_unchanged():
    # Fetch initial read-only financial data
    exc_before = client.get("/api/v1/exceptions/EXC-10031").json()
    bank_amt = exc_before["bank_amount"]
    merch_amt = exc_before["merchant_amount"]
    diff_amt = exc_before["amount_difference"]
    reason = exc_before["reason_code"]

    # Perform triage operations (Assign, Note, Review, Resolve)
    client.post("/api/v1/exceptions/EXC-10031/assign", json={"assignee": "analyst01"})
    client.post("/api/v1/exceptions/EXC-10031/notes", json={"author": "analyst01", "note_text": "Investigating..."})
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    client.post("/api/v1/exceptions/EXC-10031/status", json={
        "target_status": "RESOLVED",
        "resolution_code": "RESOLVED_VALID_TRANSACTION",
        "resolution_notes": "Resolved operational case"
    }, headers=headers)

    # Fetch updated exception object
    exc_after = client.get("/api/v1/exceptions/EXC-10031").json()

    # STRICT ASSERTION: Financial reconciliation results MUST BE READ-ONLY and UNCHANGED!
    assert exc_after["bank_amount"] == bank_amt
    assert exc_after["merchant_amount"] == merch_amt
    assert exc_after["amount_difference"] == diff_amt
    assert exc_after["reason_code"] == reason

def test_tc_p4_17_verify_dashboard_exception_metrics():
    res = client.get("/api/v1/exceptions/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_exceptions"] == 30
    assert data["unassigned_count"] == 30
    assert data["open_financial_exposure"] == 54913.50

def test_tc_p4_18_verify_local_demo_triage_workflow():
    # Verify legacy batch exceptions endpoint integrates cleanly with repository
    res = client.get("/api/batches/FINREC-20260922-001/exceptions")
    assert res.status_code == 200
    data = res.json()
    assert "exceptions" in data
    assert len(data["exceptions"]) == 30

def test_tc_p4_19_verify_unknown_exception_returns_404():
    res = client.get("/api/v1/exceptions/EXC-99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]
