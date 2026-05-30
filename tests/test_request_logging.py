import logging

from fastapi.testclient import TestClient

from main import create_app


def test_request_logging_emits_access_log(monkeypatch, caplog) -> None:
    monkeypatch.setenv("REQUEST_LOGGING_ENABLED", "true")
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert any("GET /health -> 200" in record.getMessage() for record in caplog.records)


def test_request_logging_can_be_disabled(monkeypatch, caplog) -> None:
    monkeypatch.setenv("REQUEST_LOGGING_ENABLED", "false")
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert not any(record.name == "app.request" for record in caplog.records)
