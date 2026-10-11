import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "mode" in data
    assert data["mode"] in ["LOCAL_DEMO", "REAL_MAINFRAME"]

def test_file_validate_endpoint():
    response = client.post("/api/files/validate", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["bank_record_count"] == 100

def test_batch_creation_endpoint():
    response = client.post("/api/batches", json={"batch_description": "Integration Test Batch"})
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert data["status"] == "COMPLETED_WITH_EXCEPTIONS"
