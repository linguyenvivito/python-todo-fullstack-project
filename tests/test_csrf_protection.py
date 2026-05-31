from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.models import User
from app.slices.auth.dependencies import get_auth_service
from main import create_app


def _unique_username() -> str:
    return f"csrf_{uuid4().hex[:10]}"


class _FakeAuthService:
    def register_user(self, username: str, password: str) -> User:
        del password
        return User(id=1, username=username, password_hash="hashed")


def _client_with_fake_auth(monkeypatch) -> TestClient:
    import app.core.audit as audit_module

    monkeypatch.setattr(audit_module.audit_service, "record_event", lambda *args, **kwargs: None)

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: _FakeAuthService()
    return TestClient(app)


def test_csrf_allows_cookie_request_with_trusted_origin(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("CSRF_COOKIE_BASED_ONLY", "true")
    client = _client_with_fake_auth(monkeypatch)

    response = client.post(
        "/auth/register",
        headers={"Origin": "http://localhost:8880", "Cookie": "session=fake"},
        json={"username": _unique_username(), "password": "password123"},
    )

    assert response.status_code == 201


def test_csrf_blocks_cookie_request_with_disallowed_origin(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("CSRF_COOKIE_BASED_ONLY", "true")
    client = _client_with_fake_auth(monkeypatch)

    response = client.post(
        "/auth/register",
        headers={"Origin": "http://evil.example", "Cookie": "session=fake"},
        json={"username": _unique_username(), "password": "password123"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF validation failed"}


def test_csrf_blocks_cookie_request_when_origin_and_referer_missing(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("CSRF_COOKIE_BASED_ONLY", "true")
    client = _client_with_fake_auth(monkeypatch)

    response = client.post(
        "/auth/register",
        headers={"Cookie": "session=fake"},
        json={"username": _unique_username(), "password": "password123"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "CSRF validation failed: missing origin"}


def test_csrf_allows_cookie_request_with_trusted_referer(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("CSRF_COOKIE_BASED_ONLY", "true")
    client = _client_with_fake_auth(monkeypatch)

    response = client.post(
        "/auth/register",
        headers={"Referer": "http://localhost:8880/some/page", "Cookie": "session=fake"},
        json={"username": _unique_username(), "password": "password123"},
    )

    assert response.status_code == 201


def test_csrf_cookie_only_mode_skips_requests_without_cookie(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CSRF_ENABLED", "true")
    monkeypatch.setenv("CSRF_COOKIE_BASED_ONLY", "true")
    client = _client_with_fake_auth(monkeypatch)

    response = client.post(
        "/auth/register",
        json={"username": _unique_username(), "password": "password123"},
    )

    assert response.status_code == 201


def test_csrf_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    monkeypatch.setenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CSRF_ENABLED", "false")
    monkeypatch.setenv("CSRF_COOKIE_BASED_ONLY", "true")
    client = _client_with_fake_auth(monkeypatch)

    response = client.post(
        "/auth/register",
        headers={"Origin": "http://evil.example", "Cookie": "session=fake"},
        json={"username": _unique_username(), "password": "password123"},
    )

    assert response.status_code == 201
