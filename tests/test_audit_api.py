import os

import pytest

from fastapi.testclient import TestClient

from app.core.database import init_database

if not os.getenv("DATABASE_URL", "").strip():
    pytest.skip("DATABASE_URL is required for integration tests", allow_module_level=True)

from main import app  # noqa: E402


def _reset_db() -> None:
    init_database()


def _auth_headers(client: TestClient) -> dict[str, str]:
    client.post("/auth/register", json={"username": "auditor", "password": "password123"})
    login = client.post("/auth/login", json={"username": "auditor", "password": "password123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_audit_logs_endpoint_requires_authentication() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.get("/audit-logs")
    assert response.status_code == 401


def test_audit_logs_list_and_filtering() -> None:
    _reset_db()
    client = TestClient(app)

    headers = _auth_headers(client)

    client.post("/auth/login", json={"username": "auditor", "password": "wrong-pass"})
    task = client.post("/tasks", json={"title": "Inspect logs", "description": "audit"}, headers=headers)
    assert task.status_code == 201

    all_logs = client.get("/audit-logs?limit=20&offset=0", headers=headers)
    assert all_logs.status_code == 200
    all_payload = all_logs.json()
    assert all_payload["total"] >= 3
    assert len(all_payload["items"]) >= 3

    filtered = client.get("/audit-logs?action=auth.login&success=false&limit=20", headers=headers)
    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert filtered_payload["total"] >= 1
    assert all(item["action"] == "auth.login" for item in filtered_payload["items"])
    assert all(item["success"] is False for item in filtered_payload["items"])
