import pytest
import os, sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

SUPERVISOR_HEADERS = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
ANALYST_HEADERS = {"X-User-Name": "ANALYST_01", "X-User-Role": "ANALYST"}

# ============================================================
# FEATURE A: SELF-HEALING FINANCIAL CONTROL & BATCH RECOVERY
# ============================================================

def test_feature_a_01_get_batch_checkpoints():
    response = client.get("/api/v1/batches/FINREC-20260922-001/controls")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 8
    stage_names = [stage["stage_name"] for stage in data]
    assert "INPUT_VALIDATION" in stage_names
    assert "DFSORT_DEDUP" in stage_names
    assert "COBOL_RECONCILIATION" in stage_names

def test_feature_a_02_simulate_control_failure_supervisor_only():
    # Analyst attempt should fail with 403
    analyst_resp = client.post(
        "/api/v1/recovery/simulate-failure",
        json={"batch_id": "FINREC-20260922-001", "stage": "DFSORT_DEDUP", "failure_type": "AMOUNT_CONTROL_MISMATCH"},
        headers=ANALYST_HEADERS
    )
    assert analyst_resp.status_code == 403

    # Supervisor attempt should succeed
    sup_resp = client.post(
        "/api/v1/recovery/simulate-failure",
        json={"batch_id": "FINREC-20260922-001", "stage": "DFSORT_DEDUP", "failure_type": "AMOUNT_CONTROL_MISMATCH"},
        headers=SUPERVISOR_HEADERS
    )
    assert sup_resp.status_code == 200
    data = sup_resp.json()
    assert data["control_status"] == "FAILED_CONTROL"
    assert data["recovery_status"] == "CONTROL_FAILURE"
    assert data["output_amount_total"] == 56000.00

def test_feature_a_03_recover_batch_workflow():
    response = client.post(
        "/api/v1/batches/FINREC-20260922-001/recover",
        headers=SUPERVISOR_HEADERS
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recovery_status"] == "RECOVERED"
    assert data["attempts"] >= 1
    
    # Check that stage is recovered
    chks = data["checkpoints"]
    dfsort_chk = next(c for c in chks if c["stage_name"] == "DFSORT_DEDUP")
    assert dfsort_chk["control_status"] == "RECOVERED"
    assert dfsort_chk["output_amount_total"] == 62525.00

def test_feature_a_04_recovery_audit_event_logged():
    response = client.get("/api/v1/batches/FINREC-20260922-001/recovery")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1

# ============================================================
# FEATURE B: TRANSACTION LINEAGE GRAPH
# ============================================================

def test_feature_b_01_get_transaction_lineage():
    response = client.get("/api/v1/transactions/TXN10031/lineage")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TXN10031"
    assert len(data["events"]) >= 4
    event_types = [e["event_type"] for e in data["events"]]
    assert "INPUT_RECEIVED" in event_types
    assert "VALIDATED" in event_types
    assert "MISMATCH_DETECTED" in event_types

def test_feature_b_02_explain_decision():
    response = client.get("/api/v1/transactions/TXN10031/explain-decision")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TXN10031"
    assert data["reason_code"] == "RCN-101"
    assert data["bank_amount"] == 1250.50
    assert data["merchant_amount"] == 1500.00
    assert data["amount_difference"] == 249.50

# ============================================================
# FEATURE C: INTELLIGENT HYBRID RECONCILIATION
# ============================================================

def test_feature_c_01_exact_match_bypasses_intelligent_engine():
    response = client.get("/api/v1/transactions/TXN10001/match-analysis")
    assert response.status_code == 200
    data = response.json()
    assert "MATCHED" in data["deterministic_result"]

def test_feature_c_02_unmatched_invokes_intelligent_matching():
    response = client.get("/api/v1/transactions/TXN10031/match-analysis")
    assert response.status_code == 200
    data = response.json()
    assert data["intelligent_analysis"] is not None
    ia = data["intelligent_analysis"]
    assert ia["confidence_score"] >= 0.90
    assert ia["decision"] == "AUTO_MATCH"
    assert ia["confidence_classification"] == "HIGH"
    assert ia["feature_scores"]["amount_similarity"] > 0

def test_feature_c_03_list_intelligent_matches():
    response = client.get("/api/v1/reconciliation/FINREC-20260922-001/intelligent-matches")
    assert response.status_code == 200
    matches = response.json()
    assert len(matches) >= 3
    assert matches[0]["model_version"] == "v1.0-explainable-hybrid"
