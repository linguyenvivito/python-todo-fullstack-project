import os

import pytest

from fastapi.testclient import TestClient

from app.core.database import init_database

if not os.getenv("DATABASE_URL", "").strip():
    pytest.skip("DATABASE_URL is required for integration tests", allow_module_level=True)

from main import app  # noqa: E402


def _reset_db() -> None:
    init_database()


def test_register_login_and_refresh_flow() -> None:
    _reset_db()
    client = TestClient(app)

    register_response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "password123"},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "password123"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()

    assert login_payload["access_token"]
    assert login_payload["refresh_token"]
    assert login_payload["token_type"] == "bearer"
    assert login_payload["user"]["username"] == "alice"

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_payload["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()

    assert refresh_payload["access_token"]
    assert refresh_payload["refresh_token"]
    assert refresh_payload["refresh_token"] != login_payload["refresh_token"]
    assert refresh_payload["access_token"] != login_payload["access_token"]
    assert refresh_payload["user"]["username"] == "alice"


def test_refresh_rejects_reuse_and_revokes_rotated_tokens() -> None:
    _reset_db()
    client = TestClient(app)

    client.post(
        "/auth/register",
        json={"username": "carol", "password": "password123"},
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "carol", "password": "password123"},
    )
    original_refresh_token = login_response.json()["refresh_token"]

    first_rotation = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert first_rotation.status_code == 200
    rotated_refresh_token = first_rotation.json()["refresh_token"]

    reused_response = client.post(
        "/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert reused_response.status_code == 401

    compromised_response = client.post(
        "/auth/refresh",
        json={"refresh_token": rotated_refresh_token},
    )
    assert compromised_response.status_code == 401


def test_refresh_rejects_invalid_token() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "not-a-valid-token"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"


def test_refresh_rejects_access_token() -> None:
    _reset_db()
    client = TestClient(app)

    client.post(
        "/auth/register",
        json={"username": "bob", "password": "password123"},
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "bob", "password": "password123"},
    )
    login_payload = login_response.json()

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_payload["access_token"]},
    )
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid refresh token"


def test_revoke_endpoint_invalidates_refresh_token() -> None:
    _reset_db()
    client = TestClient(app)

    client.post(
        "/auth/register",
        json={"username": "dave", "password": "password123"},
    )
    login_response = client.post(
        "/auth/login",
        json={"username": "dave", "password": "password123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    revoke_response = client.post(
        "/auth/revoke",
        json={"refresh_token": refresh_token},
    )
    assert revoke_response.status_code == 204

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


def test_register_sanitizes_username_html() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={"username": "<b>Alice</b>", "password": "password123"},
    )
    assert response.status_code == 201
    assert response.json()["username"] == "alice"
