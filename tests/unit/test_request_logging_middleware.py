import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_logging import RequestLoggingMiddleware


def test_request_logging_logs_exception_branch(caplog) -> None:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware, enabled=True)

    @app.get("/boom")
    def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    caplog.set_level(logging.ERROR, logger="app.request")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/boom")

    assert response.status_code == 500
    assert any("GET /boom failed after" in record.getMessage() for record in caplog.records)
