import pytest
import sys, os

# Add paths for backend and data
sys.path.insert(0, r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\backend")
sys.path.insert(0, r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")

from app.main import app
from fastapi.testclient import TestClient
from app.adapters.local_demo import LocalDemoAdapter
from app.models.schemas import ReasonCodeEnum, SeverityEnum

client = TestClient(app)

def test_p3_01_equal_totals_accounting_equation():
    adapter = LocalDemoAdapter(data_dir=r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    batch = adapter.submit_batch("FINREC-TEST-P3-01")
    assert batch.financial_controls is not None
    fc = batch.financial_controls
    assert fc.bank_total_amount == 94136.00
    assert fc.merch_total_amount == 60817.50
    assert fc.accounting_equation_balanced is True

def test_p3_02_amount_mismatch_rcn101():
    adapter = LocalDemoAdapter(data_dir=r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    adapter.submit_batch("FINREC-TEST-P3-02")
    ex = adapter.get_exceptions("FINREC-TEST-P3-02")
    amt_mismatches = [e for e in ex["exceptions"] if e["exception_code"] == ReasonCodeEnum.RCN_101]
    assert len(amt_mismatches) == 5
    for item in amt_mismatches:
        assert item["amount_difference"] == 249.50
        assert item["exception_type"] == "AMOUNT-MISMATCH"

def test_p3_03_missing_bank_rcn103():
    adapter = LocalDemoAdapter(data_dir=r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    adapter.submit_batch("FINREC-TEST-P3-03")
    ex = adapter.get_exceptions("FINREC-TEST-P3-03")
    missing_bank = [e for e in ex["exceptions"] if e["exception_code"] == ReasonCodeEnum.RCN_103]
    assert len(missing_bank) == 10
    for item in missing_bank:
        assert item["severity"] == SeverityEnum.CRITICAL

def test_p3_04_missing_merch_rcn104():
    adapter = LocalDemoAdapter(data_dir=r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    adapter.submit_batch("FINREC-TEST-P3-04")
    ex = adapter.get_exceptions("FINREC-TEST-P3-04")
    missing_merch = [e for e in ex["exceptions"] if e["exception_code"] == ReasonCodeEnum.RCN_104]
    assert len(missing_merch) == 10
    for item in missing_merch:
        assert item["severity"] == SeverityEnum.CRITICAL

def test_p3_05_status_mismatch_rcn102():
    adapter = LocalDemoAdapter(data_dir=r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    adapter.submit_batch("FINREC-TEST-P3-05")
    ex = adapter.get_exceptions("FINREC-TEST-P3-05")
    stat_mismatches = [e for e in ex["exceptions"] if e["exception_code"] == ReasonCodeEnum.RCN_102]
    assert len(stat_mismatches) == 5
    for item in stat_mismatches:
        assert item["severity"] == SeverityEnum.HIGH

def test_p3_11_high_value_discrepancy_severity():
    adapter = LocalDemoAdapter(data_dir=r"C:\Users\Chira\.gemini\antigravity\scratch\FinRecon\data")
    adapter.submit_batch("FINREC-TEST-P3-11")
    ex = adapter.get_exceptions("FINREC-TEST-P3-11")
    missing_items = [e for e in ex["exceptions"] if e["amount_difference"] >= 500.00]
    for item in missing_items:
        assert item["severity"] == SeverityEnum.CRITICAL

def test_p3_12_api_financial_summary_integrity():
    res = client.get("/api/batches/FINREC-20260922-001")
    assert res.status_code == 200
    data = res.json()
    assert data["financial_controls"]["bank_total_amount"] == 94136.00
    assert data["financial_controls"]["matched_amount"] == 37515.00

def test_p3_14_local_demo_mode_verification():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["mode"] == "LOCAL_DEMO"
