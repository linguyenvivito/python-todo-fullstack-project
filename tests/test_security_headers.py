from fastapi.testclient import TestClient

from main import create_app


def test_security_headers_are_set_by_default(monkeypatch) -> None:
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "true")
    monkeypatch.setenv("SECURITY_HSTS_ENABLED", "true")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("Permissions-Policy") == "camera=(), microphone=(), geolocation=()"
    assert response.headers.get("Content-Security-Policy") == "default-src 'self'; frame-ancestors 'none'"


def test_security_headers_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "false")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Content-Type-Options" not in response.headers
    assert "X-Frame-Options" not in response.headers
    assert "Referrer-Policy" not in response.headers
    assert "Permissions-Policy" not in response.headers
    assert "Content-Security-Policy" not in response.headers


def test_docs_use_docs_compatible_csp(monkeypatch) -> None:
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "true")
    client = TestClient(create_app())

    response = client.get("/docs")

    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://fastapi.tiangolo.com" in csp
    assert "connect-src 'self' https://cdn.jsdelivr.net" in csp
    assert "'unsafe-inline'" in csp


def test_non_docs_endpoints_keep_strict_csp(monkeypatch) -> None:
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "true")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("Content-Security-Policy") == "default-src 'self'; frame-ancestors 'none'"
