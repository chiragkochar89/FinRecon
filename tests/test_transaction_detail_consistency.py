import pytest
import os, sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_txn10001_matched_detail_consistency():
    """
    Regression Test: TXN10001 (Matched Transaction)
    Verifies that the transaction detail, source bank/merchant records,
    lineage decision explanation, and AI match analysis are completely consistent.
    """
    # 1. Detail endpoint
    res_v1 = client.get("/api/v1/transactions/TXN10001")
    assert res_v1.status_code == 200
    res_api = client.get("/api/transactions/TXN10001")
    assert res_api.status_code == 200
    
    data = res_v1.json()
    assert data["transaction_id"] == "TXN10001"
    assert data["acct_no"] == "ACC100000001"
    assert data["recon_result"] == "MATCHED"
    assert data["reason_code"] == "RCN-000"
    assert data["severity"] == "LOW"
    assert data["amount_difference"] == 0.00
    assert data["bank_record"]["acct_no"] == "ACC100000001"
    assert data["bank_record"]["status"] == "AP"
    assert data["merch_record"]["status"] == "AP"

    # 2. Decision explanation endpoint
    exp_res = client.get("/api/v1/transactions/TXN10001/explain-decision")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["transaction_id"] == "TXN10001"
    assert exp_data["reason_code"] == "RCN-000"
    assert exp_data["bank_status"] == "AP"
    assert exp_data["merchant_status"] == "AP"
    assert exp_data["amount_difference"] == 0.00

    # 3. Match analysis endpoint
    ma_res = client.get("/api/v1/transactions/TXN10001/match-analysis")
    assert ma_res.status_code == 200
    ma_data = ma_res.json()
    assert "MATCHED" in ma_data["deterministic_result"]


def test_txn10036_status_mismatch_detail_consistency():
    """
    Regression Test: TXN10036 (Status Mismatch Transaction)
    Verifies that the transaction detail shows STATUS-MISMATCH, RCN-102,
    bank status AP, merchant status RJ, account ACC100000036, and that
    all modal endpoints (source records, decision explanation, match analysis)
    agree with the authoritative reconciliation result.
    """
    # 1. Detail endpoint
    res_v1 = client.get("/api/v1/transactions/TXN10036")
    assert res_v1.status_code == 200
    res_api = client.get("/api/transactions/TXN10036")
    assert res_api.status_code == 200
    
    data = res_v1.json()
    assert data["transaction_id"] == "TXN10036"
    assert data["acct_no"] == "ACC100000036"
    assert data["recon_result"] == "STATUS-MISMATCH"
    assert data["reason_code"] == "RCN-102"
    assert data["severity"] == "HIGH"
    assert data["amount_difference"] == 0.00
    assert data["bank_record"]["acct_no"] == "ACC100000036"
    assert data["bank_record"]["status"] == "AP"
    assert data["merch_record"]["status"] == "RJ"

    # 2. Decision explanation endpoint
    exp_res = client.get("/api/v1/transactions/TXN10036/explain-decision")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["transaction_id"] == "TXN10036"
    assert exp_data["reason_code"] == "RCN-102"
    assert exp_data["bank_status"] == "AP"
    assert exp_data["merchant_status"] == "RJ"
    assert exp_data["amount_difference"] == 0.00
    assert "status mismatch" in exp_data["decision"].lower()

    # 3. Match analysis endpoint
    ma_res = client.get("/api/v1/transactions/TXN10036/match-analysis")
    assert ma_res.status_code == 200
    ma_data = ma_res.json()
    assert "STATUS-MISMATCH" in ma_data["deterministic_result"]
    assert ma_data["intelligent_analysis"] is not None
    assert ma_data["intelligent_analysis"]["decision"] == "EXCEPTION"


def test_transaction_search_by_account_and_id():
    """
    Regression Test: Transaction Search Support
    Verifies that searching by exact transaction ID, account ID (e.g. ACC100000001, ACC100000036),
    or substrings returns the correct records.
    """
    # Search by exact account ID ACC100000001
    res_acc1 = client.get("/api/transactions?search=ACC100000001")
    assert res_acc1.status_code == 200
    data_acc1 = res_acc1.json()
    assert data_acc1["total"] == 1
    assert data_acc1["transactions"][0]["trxn_id"] == "TXN10001"
    assert data_acc1["transactions"][0]["acct_no"] == "ACC100000001"
    assert data_acc1["transactions"][0]["recon_result"] == "MATCHED"

    # Search by exact transaction ID TXN10001
    res_txn1 = client.get("/api/transactions?search=TXN10001")
    assert res_txn1.status_code == 200
    data_txn1 = res_txn1.json()
    assert data_txn1["total"] == 1
    assert data_txn1["transactions"][0]["trxn_id"] == "TXN10001"

    # Search by account ID ACC100000036
    res_acc36 = client.get("/api/transactions?search=ACC100000036")
    assert res_acc36.status_code == 200
    data_acc36 = res_acc36.json()
    assert data_acc36["total"] == 1
    assert data_acc36["transactions"][0]["trxn_id"] == "TXN10036"
    assert data_acc36["transactions"][0]["recon_result"] == "STATUS-MISMATCH"
    assert data_acc36["transactions"][0]["bank_status"] == "AP"
    assert data_acc36["transactions"][0]["merch_status"] == "RJ"

    # Search by transaction ID TXN10036
    res_txn36 = client.get("/api/transactions?search=TXN10036")
    assert res_txn36.status_code == 200
    data_txn36 = res_txn36.json()
    assert data_txn36["total"] == 1
    assert data_txn36["transactions"][0]["trxn_id"] == "TXN10036"

    # Filter by STATUS-MISMATCH
    res_stat = client.get("/api/transactions?status=STATUS-MISMATCH")
    assert res_stat.status_code == 200
    data_stat = res_stat.json()
    assert data_stat["total"] == 5
    for t in data_stat["transactions"]:
        assert t["recon_result"] == "STATUS-MISMATCH"
        assert t["exception_code"] == "RCN-102"
        assert t["bank_status"] == "AP"
        assert t["merch_status"] == "RJ"
