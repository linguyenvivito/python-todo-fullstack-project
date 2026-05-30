from fastapi.testclient import TestClient

from main import create_app


def test_allows_request_without_origin_header(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "true")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200


def test_allows_request_from_allowlisted_origin(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "true")
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://localhost:8880"})

    assert response.status_code == 200


def test_blocks_request_from_disallowed_origin(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "true")
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://evil.example"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Origin is not allowed"}


def test_can_disable_strict_origin_check(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "http://localhost:8880")
    monkeypatch.setenv("CORS_STRICT_ORIGIN_CHECK", "false")
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://evil.example"})

    assert response.status_code == 200
