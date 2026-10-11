import pytest
import os
import sys

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import ReasonCodeEnum

client = TestClient(app)

SUPERVISOR_HEADERS = {"X-User-Name": "finrecon_supervisor", "X-User-Role": "SUPERVISOR"}
ANALYST_HEADERS = {"X-User-Name": "finrecon_user", "X-User-Role": "USER"}

TEST_BATCH_ID = "FINREC-TEST-PIPE-001"

def test_pipeline_01_initial_pending_state():
    """Requirement 1: Unexecuted batch stages must be PENDING, not completed."""
    # Reset or initialize batch
    res_reset = client.post(f"/api/v1/batches/{TEST_BATCH_ID}/reset", headers=SUPERVISOR_HEADERS)
    assert res_reset.status_code == 200

    # Fetch checkpoints
    res = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    assert res.status_code == 200
    checkpoints = res.json()
    assert len(checkpoints) == 8

    # Verify every single stage is in PENDING state
    for chk in checkpoints:
        assert chk["control_status"] == "PENDING"
        assert chk["return_code"] == 0
        assert chk["input_record_count"] == 0
        assert chk["output_record_count"] == 0
        assert chk["input_amount_total"] == 0.0
        assert chk["output_amount_total"] == 0.0
        assert chk["completed_at"] is None

def test_pipeline_02_successful_execution_order_and_metrics():
    """Requirements 2, 3, 7: Real execution in correct sequence with accurate RC and counts."""
    # Execute batch
    res_exec = client.post(f"/api/v1/batches/{TEST_BATCH_ID}/execute", headers=SUPERVISOR_HEADERS)
    assert res_exec.status_code == 200
    batch = res_exec.json()
    assert batch["batch_id"] == TEST_BATCH_ID

    # Fetch checkpoints
    res = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    assert res.status_code == 200
    chks = {c["stage_name"]: c for c in res.json()}

    # Stage 01: Input Validation
    s1 = chks["INPUT_VALIDATION"]
    assert s1["control_status"] == "PASSED"
    assert s1["return_code"] == 0
    assert s1["input_record_count"] == 100
    assert s1["output_record_count"] == 100

    # Stage 02: DFSORT Deduplication
    s2 = chks["DFSORT_DEDUP"]
    assert s2["control_status"] == "PASSED"
    assert s2["return_code"] == 0
    assert s2["input_record_count"] == 100
    assert s2["output_record_count"] == 50
    assert s2["duplicate_count"] == 50

    # Stage 03: Merchant Sort
    s3 = chks["MERCHANT_SORT"]
    assert s3["control_status"] == "PASSED"
    assert s3["return_code"] == 0
    assert s3["input_record_count"] == 50
    assert s3["output_record_count"] == 50

    # Stage 04: COBOL Reconciliation
    # Must preserve RC=04 warning convention when exceptions are detected
    s4 = chks["COBOL_RECONCILIATION"]
    assert s4["control_status"] == "WARNING"
    assert s4["return_code"] == 4
    assert s4["matched_count"] == 30
    assert s4["mismatch_count"] == 10
    assert s4["missing_count"] == 20

    # Stage 05: REXX Processing
    s5 = chks["REXX_PROCESSING"]
    assert s5["control_status"] == "PASSED"
    assert s5["return_code"] == 0
    assert s5["input_record_count"] == 30
    assert s5["output_record_count"] == 30

    # Stage 06: JCL Control
    s6 = chks["JCL_CONTROL"]
    assert s6["control_status"] == "PASSED"
    assert s6["return_code"] == 0
    assert s6["input_record_count"] == 90
    assert s6["output_record_count"] == 90

    # Stage 07: Report Generation
    s7 = chks["REPORT_GENERATION"]
    assert s7["control_status"] == "PASSED"
    assert s7["return_code"] == 0

    # Stage 08: Final Disposition
    s8 = chks["FINAL_DISPOSITION"]
    assert s8["control_status"] == "PASSED"
    assert s8["return_code"] == 4  # Reflects warning disposition

def test_pipeline_03_repeated_execution_consistency():
    """Requirement 9: Repeated execution must succeed idempotently and consistently."""
    res_exec2 = client.post(f"/api/v1/batches/{TEST_BATCH_ID}/execute", headers=SUPERVISOR_HEADERS)
    assert res_exec2.status_code == 200

    res = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    assert res.status_code == 200
    chks = {c["stage_name"]: c for c in res.json()}
    assert chks["COBOL_RECONCILIATION"]["return_code"] == 4
    assert chks["DFSORT_DEDUP"]["control_status"] == "PASSED"
    assert chks["JCL_CONTROL"]["output_record_count"] == 90

def test_pipeline_04_failure_simulation_halts_downstream():
    """Requirement 4: Simulated failure records failed stage and halts downstream stages."""
    res_fail = client.post(
        "/api/v1/recovery/simulate-failure",
        json={"batch_id": TEST_BATCH_ID, "stage": "DFSORT_DEDUP", "failure_type": "AMOUNT_CONTROL_MISMATCH"},
        headers=SUPERVISOR_HEADERS
    )
    assert res_fail.status_code == 200
    data = res_fail.json()
    assert data["control_status"] == "FAILED_CONTROL"
    assert data["return_code"] == 12
    assert data["output_amount_total"] == 56000.00

    # Verify all downstream stages are halted and NOT marked completed
    res = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    chks = {c["stage_name"]: c for c in res.json()}

    # Upstream stage remains completed
    assert chks["INPUT_VALIDATION"]["control_status"] == "PASSED"

    # Failed stage
    assert chks["DFSORT_DEDUP"]["control_status"] == "FAILED_CONTROL"
    assert chks["DFSORT_DEDUP"]["return_code"] == 12

    # Downstream stages halted
    downstream_stages = [
        "MERCHANT_SORT", "COBOL_RECONCILIATION", "REXX_PROCESSING",
        "JCL_CONTROL", "REPORT_GENERATION", "FINAL_DISPOSITION"
    ]
    for d_stage in downstream_stages:
        assert chks[d_stage]["control_status"] == "HALTED"
        assert chks[d_stage]["control_status"] != "PASSED"
        assert chks[d_stage]["control_status"] != "COMPLETED"

def test_pipeline_05_role_based_access_control():
    """Requirement 8: Failure simulation and recovery restricted to SUPERVISOR role."""
    # Analyst cannot simulate failure
    res_denied_sim = client.post(
        "/api/v1/recovery/simulate-failure",
        json={"batch_id": TEST_BATCH_ID, "stage": "DFSORT_DEDUP", "failure_type": "AMOUNT_CONTROL_MISMATCH"},
        headers=ANALYST_HEADERS
    )
    assert res_denied_sim.status_code == 403

    # Analyst cannot trigger recovery
    res_denied_rec = client.post(
        f"/api/v1/batches/{TEST_BATCH_ID}/recover",
        headers=ANALYST_HEADERS
    )
    assert res_denied_rec.status_code == 403

def test_pipeline_06_self_healing_recovery_and_verification():
    """Requirement 5: Recovery replays stage, verifies controls, restores downstream stages."""
    res_rec = client.post(
        f"/api/v1/batches/{TEST_BATCH_ID}/recover",
        headers=SUPERVISOR_HEADERS
    )
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert rec_data["recovery_status"] == "RECOVERED"

    # Verify checkpoints
    chks = {c["stage_name"]: c for c in rec_data["checkpoints"]}
    assert chks["DFSORT_DEDUP"]["control_status"] == "RECOVERED"
    assert chks["DFSORT_DEDUP"]["return_code"] == 0
    assert chks["DFSORT_DEDUP"]["output_amount_total"] == 62525.00

    # Downstream stages resumed and completed
    assert chks["MERCHANT_SORT"]["control_status"] == "PASSED"
    assert chks["COBOL_RECONCILIATION"]["control_status"] == "WARNING"
    assert chks["JCL_CONTROL"]["control_status"] == "PASSED"
    assert chks["FINAL_DISPOSITION"]["control_status"] == "PASSED"

    # Verify recovery audit event
    res_evts = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/recovery", headers=SUPERVISOR_HEADERS)
    assert res_evts.status_code == 200
    events = res_evts.json()
    assert len(events) >= 2
    event_types = [e["event_type"] for e in events]
    assert "FAILURE_SIMULATED" in event_types
    assert "RECOVERY_SUCCESS" in event_types

def test_pipeline_07_persistence_consistency_on_refresh():
    """Requirement 6: Fetching checkpoints multiple times returns consistent state."""
    r1 = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    r2 = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()

def test_pipeline_08_reset_pipeline_returns_to_pending():
    """Requirement 1, 6: Resetting returns all checkpoints to PENDING."""
    res_reset = client.post(f"/api/v1/batches/{TEST_BATCH_ID}/reset", headers=SUPERVISOR_HEADERS)
    assert res_reset.status_code == 200

    res = client.get(f"/api/v1/batches/{TEST_BATCH_ID}/controls", headers=SUPERVISOR_HEADERS)
    assert res.status_code == 200
    for chk in res.json():
        assert chk["control_status"] == "PENDING"
