import os
import sys
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.adapters.local_demo import LocalDemoAdapter
from app.repositories.exception_repository import exception_repo

client = TestClient(app)

def test_financial_totals_and_equation_conservation():
    adapter = LocalDemoAdapter("data")
    res = adapter.get_batch_status("FINREC-20260922-001")
    fin = res.financial_controls

    assert fin.bank_record_count == 50
    assert fin.merch_record_count == 50
    assert fin.bank_total_amount == 94136.00
    assert fin.merch_total_amount == 60817.50
    assert fin.matched_amount == 37515.00
    assert fin.total_exception_amount == 54913.50
    assert fin.overall_amount_difference == 33318.50
    assert fin.accounting_equation_balanced is True

def test_dynamic_batch_report_content():
    response = client.get(
        "/api/batches/FINREC-20260922-001/reports",
        headers={"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    )
    assert response.status_code == 200
    data = response.json()
    report_text = data["report"]

    assert "FINREC-20260922-001" in report_text
    assert "94,136.00" in report_text
    assert "60,817.50" in report_text
    assert "37,515.00" in report_text
    assert "33,318.50" in report_text
    assert "54,913.50" in report_text
    assert "26,257.50" not in report_text
    assert "FINREC-BATCH-001" not in report_text

def test_http_403_error_response_detail():
    res1 = client.post(
        "/api/recovery/simulate-failure",
        json={"batch_id": "FINREC-20260922-001", "stage": "DFSORT_DEDUP", "failure_type": "AMOUNT_CONTROL_MISMATCH"},
        headers={"X-User-Name": "ANALYST_01", "X-User-Role": "ANALYST"}
    )
    assert res1.status_code == 403
    assert "Operation restricted to SUPERVISOR role" in res1.json()["detail"]

    res2 = client.post(
        "/api/batches/FINREC-20260922-001/recover",
        headers={"X-User-Name": "ANALYST_01", "X-User-Role": "ANALYST"}
    )
    assert res2.status_code == 403
    assert "Operation restricted to SUPERVISOR role" in res2.json()["detail"]

from app.db.database import get_db_connection
from app.models.schemas import ResolutionCodeEnum, TriageStatusEnum

def test_assignee_lifecycle_preservation():
    target_id = "EXC-10050"
    try:
        # 1. Assign unassigned exception to ANALYST_01
        assigned = exception_repo.assign(target_id, "ANALYST_01", actor="ANALYST_01", role="ANALYST")
        assert assigned is not None
        assert assigned.assigned_to == "ANALYST_01"
        assert assigned.triage_status == TriageStatusEnum.IN_REVIEW

        # 2. Resolve as SUPERVISOR_01 and verify ANALYST_01 remains assigned_to
        resolved = exception_repo.update_status(
            target_id,
            target_status=TriageStatusEnum.RESOLVED,
            resolution_code=ResolutionCodeEnum.RESOLVED_DATA_CORRECTION,
            resolution_notes="Validated adjustment by supervisor",
            actor="SUPERVISOR_01",
            role="SUPERVISOR"
        )
        assert resolved.assigned_to == "ANALYST_01"
        assert resolved.triage_status == TriageStatusEnum.RESOLVED
    finally:
        # Restore original state in SQLite DB for test repeatability
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE exceptions SET triage_status = 'UNASSIGNED', assigned_to = NULL, resolved_at = NULL, resolution_code = NULL, resolution_notes = NULL WHERE exception_id = ?",
            (target_id,)
        )
        conn.commit()
        conn.close()

from app.models.schemas import FinancialControlTotalModel

def test_report_formatting_with_arbitrary_control_totals():
    """Verify _format_report formats dynamically from the passed FinancialControlTotalModel."""
    adapter = LocalDemoAdapter("data")
    custom_controls = FinancialControlTotalModel(
        bank_record_count=100,
        bank_total_amount=150000.50,
        merch_record_count=100,
        merch_total_amount=148000.25,
        matched_count=80,
        matched_amount=120000.00,
        amount_mismatch_count=10,
        amount_mismatch_amount=15000.00,
        status_mismatch_count=5,
        missing_bank_count=5,
        missing_bank_amount=8000.25,
        missing_merch_count=5,
        missing_merch_amount=10000.50,
        total_exception_count=20,
        total_exception_amount=30000.50,
        overall_amount_difference=2000.25,
        control_status="WARNING (EXCEPTIONS DETECTED)",
        accounting_equation_balanced=True
    )
    report = adapter._format_report("BATCH-CUSTOM-TEST", custom_controls, "2026-10-15")
    assert "BATCH-CUSTOM-TEST" in report
    assert "2026-10-15" in report
    assert "150,000.50" in report
    assert "148,000.25" in report
    assert "120,000.00" in report
    assert "2,000.25" in report
    assert "18,000.75" in report
    assert "30,000.50" in report
    assert "PASSED (BALANCED)" in report
    assert "WARNING - EXCEPTIONS DETECTED (RC=04)" in report

def test_missing_input_feeds_raises_actionable_error():
    """Verify missing input feeds fail with an actionable FileNotFoundError and do not fabricate fake totals."""
    non_existent_dir = "non_existent_demo_data_dir"
    adapter = LocalDemoAdapter(non_existent_dir)

    with pytest.raises(FileNotFoundError) as exc_info:
        adapter.submit_batch("FINREC-FAIL-TEST")

    err_msg = str(exc_info.value)
    assert "Missing required reconciliation feed files" in err_msg
    assert "Bank feed" in err_msg
    assert "Merchant feed" in err_msg
    assert "LOCAL_DEMO mode" in err_msg

def test_reconciliation_results_strict_engine_alignment():
    """Verify batch response financial controls strictly reflect reconciliation engine calculations."""
    from app.services.feed_parser import feed_parser
    from app.services.reconciliation_engine import recon_engine

    adapter = LocalDemoAdapter("data")
    res = adapter.get_batch_status("FINREC-20260922-001")
    assert res is not None

    b_recs, _ = feed_parser.parse_bank_file(adapter._get_bank_path())
    m_recs, _ = feed_parser.parse_merchant_file(adapter._get_merch_path())
    expected_controls, _ = recon_engine.reconcile_feeds(b_recs, m_recs, batch_id="FINREC-20260922-001")

    assert res.financial_controls.bank_total_amount == expected_controls.bank_total_amount
    assert res.financial_controls.merch_total_amount == expected_controls.merch_total_amount
    assert res.financial_controls.matched_amount == expected_controls.matched_amount
    assert res.financial_controls.total_exception_amount == expected_controls.total_exception_amount
    assert res.financial_controls.overall_amount_difference == expected_controls.overall_amount_difference
    assert res.financial_controls.accounting_equation_balanced == expected_controls.accounting_equation_balanced


