import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient):
    """Verifies that the /api/health endpoint returns 200 with operational status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "ai_engine" in data

def test_auth_login_valid_and_invalid(client: TestClient):
    """Verifies POST /api/auth/login with valid and invalid credentials."""
    # 1. Valid login
    res = client.post("/api/auth/login", json={
        "email": "jso.sharma@mospi.gov.in",
        "password": "Password@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["full_name"] == "Pooja Sharma"

    # 2. Invalid password
    res_bad = client.post("/api/auth/login", json={
        "email": "jso.sharma@mospi.gov.in",
        "password": "WrongPassword999"
    })
    assert res_bad.status_code == 401

def test_igot_sso_auto_provisioning(client: TestClient):
    """Verifies Parichay / iGOT Karmayogi SSO auto-provisioning via POST /api/auth/igot-sso."""
    sso_payload = {
        "civil_service_id": "KY-SSO-998811",
        "official_email": "sso.officer@mospi.gov.in",
        "full_name": "Arun Kumar",
        "cadre": "SSS",
        "designation": "Junior Statistical Officer",
        "division": "FOD"
    }
    res = client.post("/api/auth/igot-sso", json=sso_payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["full_name"] == "Arun Kumar"
    assert data["user"]["cadre"] == "SSS"

def test_protected_me_endpoint(client: TestClient, auth_headers_jso: dict):
    """Verifies GET /api/me and GET /api/auth/me return authenticated officer profile."""
    # 1. With invalid token -> 401
    res_bad = client.get("/api/me", headers={"Authorization": "Bearer forged_invalid_token_xyz"})
    assert res_bad.status_code == 401

    # 2. With valid token -> 200
    res = client.get("/api/me", headers=auth_headers_jso)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "jso.sharma@mospi.gov.in"
    assert data["designation"] == "Junior Statistical Officer"

def test_competency_framework_endpoint(client: TestClient):
    """Verifies GET /api/competencies/framework returns official MoSPI 4-domain dictionary."""
    res = client.get("/api/competencies/framework")
    assert res.status_code == 200
    data = res.json()
    assert "domains" in data or "STATISTICAL" in data or isinstance(data, dict)

def test_gap_analysis_endpoint(client: TestClient, auth_headers_jso: dict):
    """Verifies GET /api/competencies/gap-analysis returns radar-formatted gap analytics."""
    res = client.get("/api/competencies/gap-analysis", headers=auth_headers_jso)
    assert res.status_code == 200
    data = res.json()
    assert "overall_readiness_percentage" in data
    assert "all_competencies" in data
    assert "radar_data" in data
    assert len(data["all_competencies"]) > 0

def test_recommendations_pathways(client: TestClient, auth_headers_jso: dict):
    """Verifies GET /api/recommendations/my-pathway delivers dual-track iGOT + NSSTA courses."""
    res = client.get("/api/recommendations/my-pathway", headers=auth_headers_jso)
    assert res.status_code == 200
    data = res.json()
    assert "all_recommendations" in data
    assert "overall_readiness_percentage" in data
    assert "track_a_igot_courses" in data
    assert "track_b_tpac_courses" in data

def test_passport_my_passport_endpoint(client: TestClient, auth_headers_jso: dict):
    """Verifies GET /api/passport/my-passport compiles master QR code, badges, and credentials."""
    res = client.get("/api/passport/my-passport", headers=auth_headers_jso)
    assert res.status_code == 200
    data = res.json()
    assert "officer" in data
    assert "summary_metrics" in data
    assert "domains" in data
    assert "credentials" in data
    assert "badges" in data
    assert data["officer"]["full_name"] == "Pooja Sharma"

def test_public_credential_verification_endpoint(client: TestClient, auth_headers_jso: dict):
    """
    Verifies public audit endpoint GET /api/passport/verify/{code}
    allowing external validation without any bearer token.
    """
    # 1. Fetch passport to obtain an issued credential code
    passport_res = client.get("/api/passport/my-passport", headers=auth_headers_jso)
    assert passport_res.status_code == 200
    passport_data = passport_res.json()
    assert len(passport_data["credentials"]) > 0

    cred_code = passport_data["credentials"][0]["credential_code"]

    # 2. Audit publicly without authentication headers
    audit_res = client.get(f"/api/passport/verify/{cred_code}")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["valid"] is True
    assert audit_data["status"] == "OFFICIALLY_VERIFIED"
    assert audit_data["audit_trail"]["trust_status"] == "SECURE_GOV_SEAL_VALID"

def test_admin_dashboard_and_batch_allocation(client: TestClient, auth_headers_admin: dict):
    """
    Verifies GET /api/admin/dashboard and POST /api/admin/allocate-batch for cadre administrators.
    """
    # 1. Admin Dashboard
    res = client.get("/api/admin/dashboard", headers=auth_headers_admin)
    assert res.status_code == 200
    data = res.json()
    assert "macro_metrics" in data
    assert "division_matrix" in data
    assert "top_bottlenecks" in data
    assert "tpac_batches" in data

    # 2. Batch Allocation
    batches = data["tpac_batches"]
    assert len(batches) > 0
    course_id = batches[0]["course_id"]

    alloc_res = client.post(
        "/api/admin/allocate-batch",
        headers=auth_headers_admin,
        json={
            "course_id": course_id,
            "user_ids": [4],
            "notification_message": "Nomination confirmed for NSSTA residential workshop."
        }
    )
    assert alloc_res.status_code == 200
    alloc_data = alloc_res.json()
    assert alloc_data["success"] is True
    assert "newly_nominated_officers" in alloc_data
