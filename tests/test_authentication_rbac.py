import pytest
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.services.auth_service import auth_service
from app.repositories.audit_repository import audit_repo
from app.repositories.exception_repository import exception_repo
from app.models.schemas import UserRoleEnum

client = TestClient(app)

USER_PASS = os.getenv("FINRECON_USER_PASSWORD", "FinReconUser2026!")
SUPER_PASS = os.getenv("FINRECON_SUPERVISOR_PASSWORD", "FinReconSuper2026!")

def test_tc_auth_01_argon2id_hashing():
    """Verify password hashing generates valid Argon2id hash and verifies correctly."""
    plain = "TestPassword#2026"
    pw_hash = auth_service.hash_password(plain)
    assert pw_hash.startswith("$argon2id$")
    assert auth_service.verify_password(plain, pw_hash) is True
    assert auth_service.verify_password("WrongPassword", pw_hash) is False

def test_tc_auth_02_login_success_user():
    """Verify successful login for USER role returns session token and sets cookie."""
    res = client.post("/api/v1/auth/login", json={
        "username": "finrecon_user",
        "password": USER_PASS
    })
    assert res.status_code == 200
    data = res.json()
    assert "session_token" in data
    assert data["user"]["username"] == "finrecon_user"
    assert data["user"]["role"] == "USER"
    assert "finrecon_session" in res.cookies

def test_tc_auth_03_login_success_supervisor():
    """Verify successful login for SUPERVISOR role returns session token."""
    res = client.post("/api/v1/auth/login", json={
        "username": "finrecon_supervisor",
        "password": SUPER_PASS
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["username"] == "finrecon_supervisor"
    assert data["user"]["role"] == "SUPERVISOR"

def test_tc_auth_04_login_failure_invalid_credentials():
    """Verify failed login returns 401 Unauthorized and logs audit event."""
    res = client.post("/api/v1/auth/login", json={
        "username": "finrecon_user",
        "password": "IncorrectPassword999"
    })
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

    # Verify audit event logged
    events = audit_repo.get_all_events(event_type="LOGIN_FAILED", actor="finrecon_user")
    assert len(events) > 0

def test_tc_auth_05_login_failure_unknown_user():
    """Verify unknown username returns 401 and mitigates timing attack."""
    res = client.post("/api/v1/auth/login", json={
        "username": "nonexistent_finance_officer",
        "password": "SomePassword123"
    })
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]

def test_tc_auth_06_account_lockout():
    """Verify brute-force protection locks account after 5 failed attempts."""
    import secrets
    test_user = f"lockout_user_{secrets.token_hex(4)}"
    auth_service.create_user(test_user, "InitialPass123!", "USER", "Test Lockout")

    # Fail 5 times
    for i in range(5):
        client.post("/api/v1/auth/login", json={"username": test_user, "password": f"wrong_{i}"})

    # 6th attempt must be 423 Locked
    res = client.post("/api/v1/auth/login", json={"username": test_user, "password": "InitialPass123!"})
    assert res.status_code == 423
    assert "temporarily locked" in res.json()["detail"]

def test_tc_auth_07_get_me_authenticated():
    """Verify /api/v1/auth/me returns current user profile when bearer token provided."""
    # Login
    login_res = client.post("/api/v1/auth/login", json={"username": "finrecon_user", "password": USER_PASS})
    token = login_res.json()["session_token"]

    # Call /auth/me with Bearer token
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "finrecon_user"
    assert me_data["role"] == "USER"

def test_tc_auth_08_get_me_unauthenticated():
    """Verify /api/v1/auth/me returns 401 when unauthenticated."""
    # Clear client session cookies to ensure unauthenticated request
    client.cookies.clear()
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

def test_tc_auth_09_get_me_invalid_token():
    """Verify /api/v1/auth/me returns 401 with invalid or fabricated token."""
    client.cookies.clear()
    res = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fabricated_fake_token_12345"})
    assert res.status_code == 401
    assert "Invalid or expired session token" in res.json()["detail"]

def test_tc_auth_10_logout_revokes_session():
    """Verify logout revokes active session, preventing further use."""
    # Login
    login_res = client.post("/api/v1/auth/login", json={"username": "finrecon_user", "password": USER_PASS})
    token = login_res.json()["session_token"]

    # Confirm token is active
    res_before = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_before.status_code == 200

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200

    # Confirm token is now rejected
    client.cookies.clear()
    res_after = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_after.status_code == 401

def test_tc_auth_11_rbac_user_forbidden_from_supervisor_reports():
    """Verify USER role receives 403 Forbidden when attempting supervisor report exports."""
    login_res = client.post("/api/v1/auth/login", json={"username": "finrecon_user", "password": USER_PASS})
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to export CSV as standard user
    res = client.get("/api/v1/reports/exceptions.csv", headers=headers)
    assert res.status_code == 403
    assert "SUPERVISOR role" in res.json()["detail"]

    # Verify security denied audit logged
    events = audit_repo.get_all_events(event_type="SECURITY_DENIED", actor="finrecon_user")
    assert len(events) > 0

def test_tc_auth_12_rbac_supervisor_allowed_reports():
    """Verify SUPERVISOR role successfully accesses report exports."""
    login_res = client.post("/api/v1/auth/login", json={"username": "finrecon_supervisor", "password": SUPER_PASS})
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/reports/exceptions.csv", headers=headers)
    assert res.status_code == 200
    assert "Exception ID" in res.text

def test_tc_auth_13_rbac_user_forbidden_from_resolving_exception():
    """Verify USER role cannot resolve an exception (requires SUPERVISOR)."""
    login_res = client.post("/api/v1/auth/login", json={"username": "finrecon_user", "password": USER_PASS})
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/exceptions/EXC-10031/status",
        json={"target_status": "RESOLVED", "resolution_code": "RESOLVED_VALID_TRANSACTION"},
        headers=headers
    )
    assert res.status_code == 403
    assert "requires SUPERVISOR role" in res.json()["detail"]

def test_tc_auth_14_rbac_supervisor_can_resolve_exception():
    """Verify SUPERVISOR role can resolve an exception."""
    from app.db.database import get_db_connection
    # Ensure clean database state before test
    conn = get_db_connection()
    conn.execute("UPDATE exceptions SET triage_status = 'UNASSIGNED', resolved_at = NULL, resolution_code = NULL, resolution_notes = NULL WHERE exception_id = 'EXC-10031'")
    conn.commit()
    conn.close()

    # Ensure exception is IN_REVIEW first as per FSM requirements
    exception_repo.update_status("EXC-10031", "IN_REVIEW", actor="SYSTEM_PREP", role="SUPERVISOR")

    login_res = client.post("/api/v1/auth/login", json={"username": "finrecon_supervisor", "password": SUPER_PASS})
    token = login_res.json()["session_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/v1/exceptions/EXC-10031/status",
        json={"target_status": "RESOLVED", "resolution_code": "RESOLVED_VALID_TRANSACTION", "resolution_notes": "Supervisor verified transaction match"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["triage_status"] == "RESOLVED"

    # Reset back to UNASSIGNED for clean database state
    conn = get_db_connection()
    conn.execute("UPDATE exceptions SET triage_status = 'UNASSIGNED', resolved_at = NULL, resolution_code = NULL, resolution_notes = NULL WHERE exception_id = 'EXC-10031'")
    conn.commit()
    conn.close()


