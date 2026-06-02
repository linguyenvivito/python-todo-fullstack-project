from contextlib import contextmanager

from fastapi.testclient import TestClient

from main import create_app


def test_metrics_endpoint_exposes_prometheus_payload(monkeypatch) -> None:
    monkeypatch.setenv("METRICS_ENABLED", "true")
    monkeypatch.setenv("READINESS_CHECK_DATABASE", "false")

    client = TestClient(create_app())
    client.get("/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "http_requests_total" in response.text


def test_metrics_endpoint_can_be_disabled(monkeypatch) -> None:
    monkeypatch.setenv("METRICS_ENABLED", "false")
    monkeypatch.setenv("READINESS_CHECK_DATABASE", "false")

    client = TestClient(create_app())
    response = client.get("/metrics")

    assert response.status_code == 404


def test_ready_reports_ok_when_database_probe_succeeds(monkeypatch) -> None:
    monkeypatch.setenv("READINESS_CHECK_DATABASE", "true")

    class FakeCursor:
        def execute(self, _query: str) -> None:
            return None

        def close(self) -> None:
            return None

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

        def close(self) -> None:
            return None

    @contextmanager
    def fake_get_connection():
        yield FakeConnection()

    monkeypatch.setattr("main.get_connection", fake_get_connection)

    client = TestClient(create_app())
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_ready_reports_error_when_database_probe_fails(monkeypatch) -> None:
    monkeypatch.setenv("READINESS_CHECK_DATABASE", "true")

    @contextmanager
    def failing_get_connection():
        raise RuntimeError("db down")
        yield

    monkeypatch.setattr("main.get_connection", failing_get_connection)

    client = TestClient(create_app())
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "error"}}


def test_ready_reports_skipped_when_database_probe_disabled(monkeypatch) -> None:
    monkeypatch.setenv("READINESS_CHECK_DATABASE", "false")

    client = TestClient(create_app())
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "skipped"}}
