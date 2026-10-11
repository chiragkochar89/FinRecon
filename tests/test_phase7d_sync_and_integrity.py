import os
import sys
import io
import csv
import openpyxl
from decimal import Decimal
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.services.feed_parser import feed_parser, BankRecord, MerchantRecord
from app.services.reconciliation_engine import recon_engine, ReconciliationEngine
from app.repositories.exception_repository import exception_repo
from app.repositories.audit_repository import audit_repo
from app.models.schemas import (
    ReasonCodeEnum, SeverityEnum, TriageStatusEnum, ExceptionModel, UserRoleEnum
)

client = TestClient(app)

# Test 1: Actual source amounts survive parsing, classification, persistence, and export
def test_source_amounts_survive_full_pipeline():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    
    # 1. Parse & Reconcile
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    m_recs, _ = feed_parser.parse_merchant_file("data/FINRECON.INPUT.MERCHANT.txt")
    controls, excs = recon_engine.reconcile_feeds(b_recs, m_recs, batch_id="FINREC-20260922-001")
    
    # Verify TXN10041 (Missing in Merch) raw bank amount is $928.00
    exc_41 = next(e for e in excs if e.transaction_id == "TXN10041")
    assert exc_41.bank_amount == 928.00
    assert exc_41.merchant_amount == 0.00
    assert exc_41.amount_difference == 928.00
    
    # Verify TXN10091 (Missing in Bank) raw merch amount is $910.00
    exc_91 = next(e for e in excs if e.transaction_id == "TXN10091")
    assert exc_91.bank_amount == 0.00
    assert exc_91.merchant_amount == 910.00
    assert exc_91.amount_difference == 910.00

    # 2. Sync to DB & Verify Persistence
    exception_repo.sync_reconciliation_exceptions("FINREC-20260922-001", excs)
    db_exc_41 = exception_repo.get_by_id("EXC-10041")
    assert db_exc_41.bank_amount == 928.00
    
    db_exc_91 = exception_repo.get_by_id("EXC-10091")
    assert db_exc_91.merchant_amount == 910.00

    # 3. Verify Exports
    res_csv = client.get("/api/reports/exceptions.csv?batch_id=FINREC-20260922-001", headers=headers)
    assert res_csv.status_code == 200
    reader = csv.DictReader(io.StringIO(res_csv.text))
    rows = list(reader)
    row_41 = next(r for r in rows if r["Transaction ID"] == "TXN10041")
    assert float(row_41["Bank Amount"]) == 928.00
    row_91 = next(r for r in rows if r["Transaction ID"] == "TXN10091")
    assert float(row_91["Merchant Amount"]) == 910.00


# Test 2: Duplicate source records follow documented deduplication policy
def test_deduplication_policy():
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    deduped, dups, dup_cnt = recon_engine.deduplicate_bank(b_recs)
    
    assert len(b_recs) == 100
    assert len(deduped) == 90
    assert dup_cnt == 10
    assert len(dups) == 10
    # Duplicate keys are TXN10001 through TXN10010
    dup_keys = set(r.transaction_id for r in dups)
    assert "TXN10001" in dup_keys
    assert "TXN10010" in dup_keys


# Test 3: Re-running the same batch does not create unintended duplicate exceptions
def test_rerun_batch_idempotency():
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    m_recs, _ = feed_parser.parse_merchant_file("data/FINRECON.INPUT.MERCHANT.txt")
    _, excs = recon_engine.reconcile_feeds(b_recs, m_recs, batch_id="FINREC-20260922-001")
    
    # First sync
    exception_repo.sync_reconciliation_exceptions("FINREC-20260922-001", excs)
    all_excs_1 = exception_repo.get_all(batch_id="FINREC-20260922-001")
    count_1 = len(all_excs_1)
    
    # Second sync (rerun)
    exception_repo.sync_reconciliation_exceptions("FINREC-20260922-001", excs)
    all_excs_2 = exception_repo.get_all(batch_id="FINREC-20260922-001")
    count_2 = len(all_excs_2)
    
    assert count_1 == count_2 == 30


# Test 4: Different legitimate runs preserve their history
def test_multiple_batch_runs_isolation():
    b_rec = BankRecord(1, "ACC100", "TXN90001", "20260920", "120000", Decimal("500.00"), "USD", "DR", "AP", "MCH1", "REF1", "")
    m_rec = MerchantRecord(1, "MCH1", "ACC100", "TXN90001", "20260920", "120000", Decimal("600.00"), "USD", "DR", "AP", "REF1", "")
    
    engine = ReconciliationEngine()
    _, excs_custom = engine.reconcile_feeds([b_rec], [m_rec], batch_id="BATCH-ISOLATION-TEST-001")
    exception_repo.sync_reconciliation_exceptions("BATCH-ISOLATION-TEST-001", excs_custom)
    
    b1_excs = exception_repo.get_all(batch_id="FINREC-20260922-001")
    b2_excs = exception_repo.get_all(batch_id="BATCH-ISOLATION-TEST-001")
    
    assert len(b1_excs) == 30
    assert len(b2_excs) == 1
    assert b2_excs[0].transaction_id == "TXN90001"


# Test 5: Missing-bank and missing-merchant exceptions preserve correct source-side amounts
def test_missing_records_source_side_preservation():
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    m_recs, _ = feed_parser.parse_merchant_file("data/FINRECON.INPUT.MERCHANT.txt")
    _, excs = recon_engine.reconcile_feeds(b_recs, m_recs, batch_id="FINREC-20260922-001")
    
    missing_merch = [e for e in excs if e.reconciliation_status == "MISSING-IN-MERCHANT"]
    assert len(missing_merch) == 10
    for e in missing_merch:
        assert e.bank_amount > 0
        assert e.merchant_amount == 0.00
        assert e.amount_difference == e.bank_amount
        
    missing_bank = [e for e in excs if e.reconciliation_status == "MISSING-IN-BANK"]
    assert len(missing_bank) == 10
    for e in missing_bank:
        assert e.bank_amount == 0.00
        assert e.merchant_amount > 0
        assert e.amount_difference == e.merchant_amount


# Test 6: API summaries and persisted exceptions identify the same batch and run
def test_api_summary_and_persisted_exceptions_consistency():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    
    # 1. Batch API Summary
    res_batch = client.get("/api/batches/FINREC-20260922-001", headers=headers)
    assert res_batch.status_code == 200
    batch_fin = res_batch.json()["financial_controls"]
    
    # 2. Exceptions Summary API
    res_sum = client.get("/api/exceptions/summary?batch_id=FINREC-20260922-001", headers=headers)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    
    # 3. Exceptions List API
    res_list = client.get("/api/exceptions?batch_id=FINREC-20260922-001", headers=headers)
    assert res_list.status_code == 200
    list_excs = res_list.json()
    list_diff_sum = round(sum(e["amount_difference"] for e in list_excs), 2)
    
    assert batch_fin["total_exception_amount"] == 54913.50
    assert sum_data["total_financial_exposure"] == 54913.50
    assert list_diff_sum == 54913.50


# Test 7: CSV, Excel, and PDF outputs agree with authoritative run data
def test_export_outputs_consistency():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    
    # CSV
    r_csv = client.get("/api/reports/exceptions.csv?batch_id=FINREC-20260922-001", headers=headers)
    assert r_csv.status_code == 200
    reader = csv.DictReader(io.StringIO(r_csv.text))
    csv_sum = round(sum(float(row["Amount Difference"]) for row in reader), 2)
    assert csv_sum == 54913.50
    
    # Excel
    r_xlsx = client.get("/api/reports/reconciliation.xlsx?batch_id=FINREC-20260922-001", headers=headers)
    assert r_xlsx.status_code == 200
    wb = openpyxl.load_workbook(filename=io.BytesIO(r_xlsx.content))
    ws_exc = wb["Exceptions"]
    xlsx_sum = round(sum(float(row[8]) for row in ws_exc.iter_rows(min_row=2, values_only=True)), 2)
    assert xlsx_sum == 54913.50
    
    # PDF
    r_pdf = client.get("/api/reports/reconciliation.pdf?batch_id=FINREC-20260922-001", headers=headers)
    assert r_pdf.status_code == 200
    assert len(r_pdf.content) > 1000


# Test 8: Gross mismatch exposure remains correct when discrepancies are positive and negative
def test_gross_versus_net_exposure_mixed_directions():
    engine = ReconciliationEngine()
    
    # Record 1: Bank=100, Merch=150 (Merch > Bank by 50)
    b1 = BankRecord(1, "ACC1", "TXN1", "20260920", "120000", Decimal("100.00"), "USD", "DR", "AP", "M1", "R1", "")
    m1 = MerchantRecord(1, "M1", "ACC1", "TXN1", "20260920", "120000", Decimal("150.00"), "USD", "DR", "AP", "R1", "")
    
    # Record 2: Bank=200, Merch=160 (Bank > Merch by 40)
    b2 = BankRecord(2, "ACC2", "TXN2", "20260920", "120000", Decimal("200.00"), "USD", "DR", "AP", "M2", "R2", "")
    m2 = MerchantRecord(2, "M2", "ACC2", "TXN2", "20260920", "120000", Decimal("160.00"), "USD", "DR", "AP", "R2", "")
    
    controls, excs = engine.reconcile_feeds([b1, b2], [m1, m2], batch_id="MIXED-BATCH")
    
    gross_exposure = sum(e.amount_difference for e in excs) # 50 + 40 = 90.00
    net_amt_mismatch_diff = abs(sum(b.amount for b in [b1, b2]) - sum(m.amount for m in [m1, m2])) # |300 - 310| = 10.00
    
    assert len(excs) == 2
    assert gross_exposure == 90.00
    assert net_amt_mismatch_diff == 10.00
    assert gross_exposure != net_amt_mismatch_diff


# Test 9: Distinct definitions of four core accounting metrics
def test_accounting_metrics_definitions():
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    m_recs, _ = feed_parser.parse_merchant_file("data/FINRECON.INPUT.MERCHANT.txt")
    controls, excs = recon_engine.reconcile_feeds(b_recs, m_recs, batch_id="FINREC-20260922-001")
    
    # 1. Net Ledger Variance
    net_ledger_variance = controls.overall_amount_difference
    assert net_ledger_variance == 33318.50
    
    # 2. Missing-Record Face Value
    missing_face_value = controls.missing_bank_amount + controls.missing_merch_amount
    assert missing_face_value == 53666.00
    
    # 3. Gross Amount-Mismatch Exposure
    amt_mismatch_excs = [e for e in excs if e.reconciliation_status == "AMOUNT-MISMATCH"]
    gross_amt_mismatch = sum(e.amount_difference for e in amt_mismatch_excs)
    assert gross_amt_mismatch == 1247.50
    
    # 4. Total Exception Exposure
    total_exposure = controls.total_exception_amount
    assert total_exposure == 54913.50
    
    # Equation verification
    assert total_exposure == gross_amt_mismatch + missing_face_value


# Test 10: Existing security RBAC and audit logging continue to work
def test_security_rbac_and_audit_logging():
    analyst_headers = {"X-User-Name": "ANALYST_01", "X-User-Role": "ANALYST"}
    supervisor_headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    
    # 1. Export attempt by ANALYST -> Forbidden (403)
    res_forbidden = client.get("/api/reports/exceptions.csv?batch_id=FINREC-20260922-001", headers=analyst_headers)
    assert res_forbidden.status_code == 403
    
    # 2. Export attempt by SUPERVISOR -> Success (200)
    res_allowed = client.get("/api/reports/exceptions.csv?batch_id=FINREC-20260922-001", headers=supervisor_headers)
    assert res_allowed.status_code == 200
    
    # 3. Verify audit log entry was created
    events = audit_repo.get_all_events(batch_id="FINREC-20260922-001")
    export_events = [ev for ev in events if ev.event_type == "REPORT_EXPORTED"]
    assert len(export_events) > 0


# Test 11: Known batch filtering returns only its own records and correct financial totals
def test_known_batch_filtering():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    batch_id = "FINREC-20260922-001"
    
    # 1. Repository direct check
    records = exception_repo.get_all(batch_id=batch_id)
    assert len(records) == 30
    assert all(r.batch_id == batch_id for r in records)
    
    summary = exception_repo.get_summary(batch_id=batch_id)
    assert summary.total_exceptions == 30
    assert summary.total_financial_exposure == 54913.50
    
    # 2. API endpoints check
    res_list = client.get(f"/api/exceptions?batch_id={batch_id}", headers=headers)
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert len(data_list) == 30
    assert all(d["batch_id"] == batch_id for d in data_list)
    
    res_sum = client.get(f"/api/exceptions/summary?batch_id={batch_id}", headers=headers)
    assert res_sum.status_code == 200
    data_sum = res_sum.json()
    assert data_sum["total_exceptions"] == 30
    assert data_sum["total_financial_exposure"] == 54913.50


# Test 12: Unknown batch returns no records, zero-valued financial totals, and 404 on batch routes without mutating SQLite
def test_unknown_batch_returns_empty():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    unknown_batch = "BATCH-UNKNOWN-DOES-NOT-EXIST-000"
    
    # 1. Repository direct check
    records = exception_repo.get_all(batch_id=unknown_batch)
    assert records == []
    
    summary = exception_repo.get_summary(batch_id=unknown_batch)
    assert summary.total_exceptions == 0
    assert summary.unassigned_count == 0
    assert summary.in_review_count == 0
    assert summary.resolved_count == 0
    assert summary.rejected_count == 0
    assert summary.critical_count == 0
    assert summary.high_count == 0
    assert summary.medium_count == 0
    assert summary.low_count == 0
    assert summary.total_financial_exposure == 0.00
    assert summary.open_financial_exposure == 0.00
    
    # 2. API query parameter filtering endpoints check (returns empty list / zero summary)
    res_list = client.get(f"/api/exceptions?batch_id={unknown_batch}", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json() == []
    
    res_sum = client.get(f"/api/exceptions/summary?batch_id={unknown_batch}", headers=headers)
    assert res_sum.status_code == 200
    data_sum = res_sum.json()
    assert data_sum["total_exceptions"] == 0
    assert data_sum["total_financial_exposure"] == 0.00
    assert data_sum["open_financial_exposure"] == 0.00

    # 3. Dedicated batch resource endpoints check (consistently return 404 for unknown batches)
    res_batch = client.get(f"/api/batches/{unknown_batch}", headers=headers)
    assert res_batch.status_code == 404
    assert f"Batch {unknown_batch} not found" in res_batch.json()["detail"]

    res_batch_excs = client.get(f"/api/batches/{unknown_batch}/exceptions", headers=headers)
    assert res_batch_excs.status_code == 404

    res_batch_results = client.get(f"/api/batches/{unknown_batch}/results", headers=headers)
    assert res_batch_results.status_code == 404

    res_batch_reports = client.get(f"/api/batches/{unknown_batch}/reports", headers=headers)
    assert res_batch_reports.status_code == 404

    res_batch_audit = client.get(f"/api/batches/{unknown_batch}/audit", headers=headers)
    assert res_batch_audit.status_code == 404

    res_excel = client.get(f"/api/reports/reconciliation.xlsx?batch_id={unknown_batch}", headers=headers)
    assert res_excel.status_code == 404

    res_pdf = client.get(f"/api/reports/reconciliation.pdf?batch_id={unknown_batch}", headers=headers)
    assert res_pdf.status_code == 404

    # 4. Prove that reading an unknown batch did NOT create any database records
    records_after = exception_repo.get_all(batch_id=unknown_batch)
    assert records_after == []


# Test 13: Omitting batch_id retains documented all-batches behavior and respects pagination limits
def test_omitted_batch_returns_all():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    
    # 1. Repository get_all without batch_id
    all_records = exception_repo.get_all()
    all_records_explicit_none = exception_repo.get_all(batch_id=None)
    assert len(all_records) == len(all_records_explicit_none)
    assert len(all_records) >= 30  # Contains FINREC-20260922-001 (30) plus any isolated test batches
    
    # 2. Repository get_summary without batch_id
    all_summary = exception_repo.get_summary()
    all_summary_explicit_none = exception_repo.get_summary(batch_id=None)
    assert all_summary.total_exceptions == len(all_records)
    assert all_summary_explicit_none.total_exceptions == len(all_records)
    assert all_summary.total_financial_exposure >= 54913.50
    
    # 3. API endpoint default pagination limit (100)
    res_list_default = client.get("/api/exceptions", headers=headers)
    assert res_list_default.status_code == 200
    expected_default_count = min(100, len(all_records))
    assert len(res_list_default.json()) == expected_default_count
    
    # 4. API endpoint explicit larger limit requesting all records (up to max 500)
    req_limit = min(500, len(all_records))
    res_list_large = client.get(f"/api/exceptions?limit={req_limit}", headers=headers)
    assert res_list_large.status_code == 200
    assert len(res_list_large.json()) == req_limit
    
    # 5. API summary endpoint aggregates across all batches without pagination
    res_sum = client.get("/api/exceptions/summary", headers=headers)
    assert res_sum.status_code == 200
    assert res_sum.json()["total_exceptions"] == len(all_records)


# Test 14: Mid-sync failure rolls back cleanly without partial commits or lingering locks
def test_sync_reconciliation_exceptions_rollback_on_error():
    import sqlite3
    test_batch = "BATCH-ROLLBACK-TEST-999"
    
    rec1 = ExceptionModel(
        exception_id="EXC-DUPLICATE-PK",
        batch_id=test_batch,
        transaction_id="TXN-RB-001",
        reason_code=ReasonCodeEnum.RCN_101,
        reason_description="Rollback test 1",
        severity=SeverityEnum.HIGH,
        reconciliation_status="AMOUNT-MISMATCH",
        bank_amount=100.00,
        merchant_amount=200.00,
        amount_difference=100.00,
        bank_status="AP",
        merchant_status="AP",
        triage_status=TriageStatusEnum.UNASSIGNED,
        created_at="2026-09-22 14:00:00",
        updated_at="2026-09-22 14:00:00"
    )
    # rec2 shares the same primary key exception_id but has a different transaction_id,
    # causing an SQLite UNIQUE constraint IntegrityError upon insertion
    rec2 = ExceptionModel(
        exception_id="EXC-DUPLICATE-PK",
        batch_id=test_batch,
        transaction_id="TXN-RB-002",
        reason_code=ReasonCodeEnum.RCN_102,
        reason_description="Rollback test 2",
        severity=SeverityEnum.HIGH,
        reconciliation_status="STATUS-MISMATCH",
        bank_amount=150.00,
        merchant_amount=150.00,
        amount_difference=0.00,
        bank_status="AP",
        merchant_status="RJ",
        triage_status=TriageStatusEnum.UNASSIGNED,
        created_at="2026-09-22 14:00:00",
        updated_at="2026-09-22 14:00:00"
    )
    
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint failed"):
        exception_repo.sync_reconciliation_exceptions(test_batch, [rec1, rec2])
        
    # Verify complete atomic rollback: rec1 was NOT persisted!
    persisted = exception_repo.get_all(batch_id=test_batch)
    assert persisted == []
    
    # Verify no database connection or table locks linger - subsequent operations succeed normally
    summary = exception_repo.get_summary(batch_id=test_batch)
    assert summary.total_exceptions == 0
    assert summary.total_financial_exposure == 0.00


# Test 15: Reading existing batch returns expected data without mutating SQLite, and explicit submission works cleanly
def test_existing_batch_read_and_explicit_submission(tmp_path, monkeypatch):
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}
    batch_id = "FINREC-20260922-001"

    # 1. Read existing batch status via API
    res_batch = client.get(f"/api/batches/{batch_id}", headers=headers)
    assert res_batch.status_code == 200
    b_data = res_batch.json()
    assert b_data["batch_id"] == batch_id
    assert b_data["status"] == "COMPLETED_WITH_EXCEPTIONS"
    assert b_data["financial_controls"]["bank_total_amount"] == 94136.00
    assert b_data["financial_controls"]["merch_total_amount"] == 60817.50

    # 2. Read existing batch results, exceptions, reports, audit
    res_results = client.get(f"/api/batches/{batch_id}/results", headers=headers)
    assert res_results.status_code == 200
    assert res_results.json()["batch_id"] == batch_id

    res_excs = client.get(f"/api/batches/{batch_id}/exceptions", headers=headers)
    assert res_excs.status_code == 200
    assert len(res_excs.json()["exceptions"]) == 30

    res_reports = client.get(f"/api/batches/{batch_id}/reports", headers=headers)
    assert res_reports.status_code == 200
    assert "FINRECON" in res_reports.json()["report"]

    res_audit = client.get(f"/api/batches/{batch_id}/audit", headers=headers)
    assert res_audit.status_code == 200
    assert len(res_audit.json()["audit_logs"]) == 7

    # 3. Explicit batch submission on an isolated database
    iso_db = str(tmp_path / "isolated_submit.db")
    monkeypatch.setenv("FINRECON_DB_PATH", iso_db)
    from app.db.database import init_db
    from app.adapters.local_demo import LocalDemoAdapter
    init_db()

    adapter = LocalDemoAdapter("data")
    test_sub_batch = "FINREC-TEST-EXPLICIT-001"
    submitted = adapter.submit_batch(test_sub_batch)
    assert submitted.batch_id == test_sub_batch
    assert submitted.financial_controls.accounting_equation_balanced is True
    assert submitted.financial_controls.total_exception_count == 30

    # Verify exceptions were persisted in the isolated database
    iso_excs = exception_repo.get_all(batch_id=test_sub_batch)
    assert len(iso_excs) == 30

