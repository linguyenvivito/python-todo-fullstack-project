import os
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import init_database
from main import create_app


TEST_DB = Path(__file__).with_name("test_tasks.db")
os.environ.pop("DATABASE_URL", None)
os.environ["SQLITE_DB_PATH"] = str(TEST_DB)


def _reset_db() -> None:
    if TEST_DB.exists():
        TEST_DB.unlink()
    init_database()


def test_login_rate_limit_returns_429(monkeypatch) -> None:
    _reset_db()
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_AUTH_LOGIN", "2/minute")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")

    client = TestClient(create_app())
    username = f"ratelimit_{uuid4().hex[:10]}"
    client_id = f"test-client-{uuid4().hex[:8]}"

    register_response = client.post(
        "/auth/register",
        headers={"x-client-id": client_id},
        json={"username": username, "password": "password123"},
    )
    assert register_response.status_code == 201

    login_payload = {"username": username, "password": "password123"}
    first = client.post("/auth/login", headers={"x-client-id": client_id}, json=login_payload)
    second = client.post("/auth/login", headers={"x-client-id": client_id}, json=login_payload)
    third = client.post("/auth/login", headers={"x-client-id": client_id}, json=login_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
