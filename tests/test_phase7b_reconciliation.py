import os
import tempfile
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.feed_parser import feed_parser, BankRecord, MerchantRecord
from app.services.reconciliation_engine import recon_engine, ReconciliationEngine
from app.models.schemas import ReasonCodeEnum, SeverityEnum, TriageStatusEnum

client = TestClient(app)

def test_feed_parser_valid_records():
    b_recs, b_errs = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    m_recs, m_errs = feed_parser.parse_merchant_file("data/FINRECON.INPUT.MERCHANT.txt")

    assert len(b_recs) == 100
    assert len(b_errs) == 0
    assert len(m_recs) == 50
    assert len(m_errs) == 0

    assert b_recs[0].amount == Decimal("3583.00")
    assert m_recs[0].amount == Decimal("1250.50")

def test_feed_parser_malformed_records(tmp_path):
    # Invalid length file
    bad_file = tmp_path / "bad_bank.txt"
    bad_file.write_text("ACC100000014TXN1004320260920195530000000358300USD\n") # < 80 chars
    b_recs, b_errs = feed_parser.parse_bank_file(str(bad_file))
    assert len(b_recs) == 0
    assert len(b_errs) == 1
    assert "Invalid record length" in b_errs[0]

    # Missing file
    with pytest.raises(FileNotFoundError):
        feed_parser.parse_bank_file(str(tmp_path / "non_existent.txt"))

def test_bank_feed_deduplication():
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    deduped, dups, dup_cnt = recon_engine.deduplicate_bank(b_recs)

    assert len(b_recs) == 100
    assert len(deduped) == 90
    assert dup_cnt == 10
    assert len(dups) == 10

def test_reconciliation_engine_categorization_and_equations():
    b_recs, _ = feed_parser.parse_bank_file("data/FINRECON.INPUT.BANK.txt")
    m_recs, _ = feed_parser.parse_merchant_file("data/FINRECON.INPUT.MERCHANT.txt")

    controls, exceptions = recon_engine.reconcile_feeds(b_recs, m_recs, batch_id="FINREC-20260922-001")

    assert controls.bank_record_count == 50
    assert controls.merch_record_count == 50
    assert controls.matched_count == 30
    assert controls.matched_amount == 37515.00
    assert controls.amount_mismatch_count == 5
    assert controls.status_mismatch_count == 5
    assert controls.missing_bank_count == 10
    assert controls.missing_bank_amount == 9550.00
    assert controls.missing_merch_count == 10
    assert controls.missing_merch_amount == 44116.00
    assert controls.total_exception_count == 30
    assert controls.bank_total_amount == 94136.00
    assert controls.merch_total_amount == 60817.50
    assert controls.total_exception_amount == 54913.50
    assert controls.overall_amount_difference == 33318.50
    assert controls.accounting_equation_balanced is True

def test_dual_amount_and_status_mismatch_precedence():
    # Test precedence rule: Amount Mismatch (RCN-101) takes precedence over Status Mismatch
    engine = ReconciliationEngine()
    b_rec = BankRecord(1, "ACC100", "TXN99999", "20260920", "120000", Decimal("100.00"), "USD", "DR", "AP", "MCH1", "REF1", "")
    m_rec = MerchantRecord(1, "MCH1", "ACC100", "TXN99999", "20260920", "120000", Decimal("200.00"), "USD", "DR", "RJ", "REF1", "")

    controls, excs = engine.reconcile_feeds([b_rec], [m_rec], batch_id="TEST-BATCH")
    assert len(excs) == 1
    assert excs[0].reason_code == ReasonCodeEnum.RCN_101

def test_end_to_end_api_and_export_integrity():
    headers = {"X-User-Name": "SUPERVISOR_01", "X-User-Role": "SUPERVISOR"}

    # 1. Batch API
    r1 = client.get("/api/batches/FINREC-20260922-001", headers=headers)
    assert r1.status_code == 200
    fin = r1.json()["financial_controls"]
    assert fin["bank_total_amount"] == 94136.00
    assert fin["merch_total_amount"] == 60817.50
    assert fin["accounting_equation_balanced"] is True

    # 2. Checkpoint controls
    r2 = client.get("/api/batches/FINREC-20260922-001/controls", headers=headers)
    assert r2.status_code == 200
    assert len(r2.json()) == 8

    # 3. CSV export
    r3 = client.get("/api/reports/exceptions.csv?batch_id=FINREC-20260922-001", headers=headers)
    assert r3.status_code == 200
    assert "Exception ID" in r3.text

    # 4. Excel export
    r4 = client.get("/api/reports/reconciliation.xlsx?batch_id=FINREC-20260922-001", headers=headers)
    assert r4.status_code == 200

    # 5. PDF export
    r5 = client.get("/api/reports/reconciliation.pdf?batch_id=FINREC-20260922-001", headers=headers)
    assert r5.status_code == 200
