import pytest
from fastapi.testclient import TestClient
from backend.main import app, DB_FILE
from backend.services.auth_service import get_password_hash
import sqlite3
import uuid
import json

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Clear tables for isolation
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM organizations")
    cursor.execute("DELETE FROM refresh_tokens")
    cursor.execute("DELETE FROM migration_jobs")
    conn.commit()

    # Create default org and admin
    org_id = "test_org"
    admin_id = "test_admin"
    hashed_pw = get_password_hash("password")
    
    cursor.execute("INSERT INTO organizations (id, name) VALUES (?, ?)", (org_id, "Test Org"))
    cursor.execute("INSERT INTO users (id, org_id, email, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
                   (admin_id, org_id, "admin@test.com", hashed_pw, "Admin"))
    
    conn.commit()
    conn.close()
    
    yield
    
    # Teardown
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM organizations")
    cursor.execute("DELETE FROM refresh_tokens")
    cursor.execute("DELETE FROM migration_jobs")
    conn.commit()
    conn.close()

def login(email="admin@test.com", password="password"):
    res = client.post("/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200
    return res.json()

def test_1_register():
    # 1. Test registration
    res = client.post("/auth/register", json={"email": "new@test.com", "password": "password", "role": "Admin"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "Admin"

def test_2_login():
    # 2. Test successful login
    res = client.post("/auth/login", data={"username": "admin@test.com", "password": "password"})
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.json()

def test_3_login_failure():
    # 3. Test failed login
    res = client.post("/auth/login", data={"username": "admin@test.com", "password": "wrong"})
    assert res.status_code == 401

def test_4_token_rotation():
    # 4. Test token refresh
    tokens = login()
    res = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 200
    new_tokens = res.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

def test_5_route_protection_unauthenticated():
    # 5. Test protected route without token
    res = client.get("/api/migrations/history")
    assert res.status_code == 401

def test_6_route_protection_authenticated():
    # 6. Test protected route with token
    tokens = login()
    res = client.get("/api/migrations/history", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert res.status_code == 200

def test_7_role_based_access_admin_route():
    # 7. Test Admin route as Admin
    tokens = login()
    res = client.get("/auth/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert res.status_code == 200

def test_8_role_based_access_denied():
    # 8. Test Admin route as Viewer
    client.post("/auth/register", json={"email": "viewer@test.com", "password": "password", "role": "Viewer"})
    tokens = login("viewer@test.com", "password")
    # Actually register creates an Admin in their own org, so let's invite a viewer
    admin_tokens = login()
    client.post("/auth/invite", json={"email": "invited@test.com", "password": "password", "role": "Viewer"},
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"})
    viewer_tokens = login("invited@test.com", "password")
    
    res = client.get("/auth/users", headers={"Authorization": f"Bearer {viewer_tokens['access_token']}"})
    assert res.status_code == 403

def test_9_data_isolation():
    # 9. Test Data Isolation (Org A shouldn't see Org B's jobs)
    admin_tokens = login()
    payload = {
        "source": {"db_type": "postgres", "host": "localhost", "port": 5432, "username": "u", "password": "p", "database": "db1"},
        "target": {"db_type": "mysql", "host": "localhost", "port": 3306, "username": "u", "password": "p", "database": "db2"},
        "mode": "schema_and_data"
    }
    # Create a job for admin
    client.post("/api/migrate", json=payload, 
                headers={"Authorization": f"Bearer {admin_tokens['access_token']}"})
    
    # Org A sees it
    res = client.get("/api/migrations/history", headers={"Authorization": f"Bearer {admin_tokens['access_token']}"})
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1

    # Org B registers
    client.post("/auth/register", json={"email": "org_b@test.com", "password": "password"})
    org_b_tokens = login("org_b@test.com", "password")
    
    # Org B sees 0
    res = client.get("/api/migrations/history", headers={"Authorization": f"Bearer {org_b_tokens['access_token']}"})
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0

def test_10_change_password():
    # 10. Test password change
    tokens = login()
    res = client.post("/auth/change-password", json={"old_password": "password", "new_password": "new_password"},
                      headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert res.status_code == 200
    
    # old password fails
    res = client.post("/auth/login", data={"username": "admin@test.com", "password": "password"})
    assert res.status_code == 401
    
    # new password works
    res = client.post("/auth/login", data={"username": "admin@test.com", "password": "new_password"})
    assert res.status_code == 200

def test_11_logout():
    # 11. Test logout invalidates refresh token
    tokens = login()
    client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]}, 
                headers={"Authorization": f"Bearer {tokens['access_token']}"})
    
    res = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 401

def test_12_me_endpoint():
    # 12. Test /me returns correct user
    tokens = login()
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert res.status_code == 200
    assert res.json()["email"] == "admin@test.com"

def test_13_newly_created_user_only_sees_own_records():
    # Register user A and get their org_id
    client.post("/auth/register", json={"email": "userA@test.com", "password": "passwordA123!"})
    tokens_A = login("userA@test.com", "passwordA123!")
    me_A = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens_A['access_token']}"}).json()
    org_A = me_A["org_id"]

    # Register user B and get their org_id
    client.post("/auth/register", json={"email": "userB@test.com", "password": "passwordB123!"})
    tokens_B = login("userB@test.com", "passwordB123!")
    me_B = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens_B['access_token']}"}).json()
    org_B = me_B["org_id"]

    # Insert migration records directly for user A and user B
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO migration_jobs (id, org_id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("job_A", org_A, "postgres", "mysql", "SUCCESS", 5, 100, "1.2s", "2026-01-01T00:00:00", json.dumps({"id": "job_A", "status": "success"}))
    )
    cursor.execute(
        "INSERT INTO migration_logs (job_id, timestamp, level, step, message) VALUES (?, ?, ?, ?, ?)",
        ("job_A", "2026-01-01T00:00:00", "info", "init", "Started job A")
    )
    cursor.execute(
        "INSERT INTO migration_jobs (id, org_id, source_db, target_db, status, tables_migrated, rows_migrated, duration, timestamp, full_payload) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("job_B", org_B, "oracle", "postgres", "SUCCESS", 2, 50, "0.8s", "2026-01-01T01:00:00", json.dumps({"id": "job_B", "status": "success"}))
    )
    conn.commit()
    conn.close()

    # User A checks history
    res_A_history = client.get("/api/migrations/history", headers={"Authorization": f"Bearer {tokens_A['access_token']}"})
    assert res_A_history.status_code == 200
    items_A = res_A_history.json()["items"]
    assert len(items_A) == 1
    assert items_A[0]["id"] == "job_A"

    # User A checks job detail endpoints for job_A
    assert client.get("/api/migrations/job_A", headers={"Authorization": f"Bearer {tokens_A['access_token']}"}).status_code == 200
    assert client.get("/api/migrations/job_A/details", headers={"Authorization": f"Bearer {tokens_A['access_token']}"}).status_code == 200
    assert client.get("/api/migrations/job_A/logs", headers={"Authorization": f"Bearer {tokens_A['access_token']}"}).status_code == 200

    # User B checks history (must NOT see job_A)
    res_B_history = client.get("/api/migrations/history", headers={"Authorization": f"Bearer {tokens_B['access_token']}"})
    assert res_B_history.status_code == 200
    items_B = res_B_history.json()["items"]
    assert len(items_B) == 1
    assert items_B[0]["id"] == "job_B"

    # User B checks job detail endpoints for job_A (must return 404 Not Found)
    assert client.get("/api/migrations/job_A", headers={"Authorization": f"Bearer {tokens_B['access_token']}"}).status_code == 404
    assert client.get("/api/migrations/job_A/details", headers={"Authorization": f"Bearer {tokens_B['access_token']}"}).status_code == 404
    assert client.get("/api/migrations/job_A/logs", headers={"Authorization": f"Bearer {tokens_B['access_token']}"}).status_code == 404
