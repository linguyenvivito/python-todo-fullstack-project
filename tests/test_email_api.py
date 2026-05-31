import os
import smtplib

import pytest

from fastapi.testclient import TestClient

from app.core.database import init_database

if not os.getenv("DATABASE_URL", "").strip():
    pytest.skip("DATABASE_URL is required for integration tests", allow_module_level=True)

from main import app  # noqa: E402


def _reset_db() -> None:
    init_database()


def _auth_headers(client: TestClient) -> dict[str, str]:
    register = client.post(
        "/auth/register",
        json={"username": "mailer", "password": "password123"},
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={"username": "mailer", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_send_email_requires_authentication() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.post(
        "/email/send",
        json={"to_email": "team@example.com", "subject": "Hello", "body": "World"},
    )
    assert response.status_code == 401


def test_list_email_templates_requires_authentication() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.get("/email/templates")
    assert response.status_code == 401


def test_list_email_templates_success() -> None:
    _reset_db()
    client = TestClient(app)
    headers = _auth_headers(client)

    response = client.get("/email/templates", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    names = {item["name"] for item in payload["items"]}
    assert "welcome" in names
    assert "password_reset" in names


def test_send_email_success_with_smtp_mock(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _auth_headers(client)

    os.environ["SMTP_HOST"] = "smtp.example.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USE_TLS"] = "true"
    os.environ["SMTP_USE_SSL"] = "false"
    os.environ["SMTP_USERNAME"] = "user@example.com"
    os.environ["SMTP_PASSWORD"] = "secret"
    os.environ["SMTP_FROM_EMAIL"] = "noreply@example.com"
    os.environ["SMTP_FROM_NAME"] = "Task API"

    sent = {"called": False, "subject": "", "to": ""}

    class DummySMTP:
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.com"
            assert int(port) == 587
            assert timeout == 10.0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            return None

        def login(self, username, password):
            assert username == "user@example.com"
            assert password == "secret"

        def send_message(self, message):
            sent["called"] = True
            sent["subject"] = message["Subject"]
            sent["to"] = message["To"]

    monkeypatch.setattr("app.slices.email.service.smtplib.SMTP", DummySMTP)

    response = client.post(
        "/email/send",
        headers=headers,
        json={"to_email": "team@example.com", "subject": "Hello", "body": "World"},
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Email sent"
    assert sent["called"] is True
    assert sent["subject"] == "Hello"
    assert sent["to"] == "team@example.com"


def test_send_templated_email_success_with_smtp_mock(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _auth_headers(client)

    os.environ["SMTP_HOST"] = "smtp.example.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USE_TLS"] = "true"
    os.environ["SMTP_USE_SSL"] = "false"
    os.environ["SMTP_USERNAME"] = "user@example.com"
    os.environ["SMTP_PASSWORD"] = "secret"
    os.environ["SMTP_FROM_EMAIL"] = "noreply@example.com"

    sent = {"called": False, "subject": "", "body": ""}

    class DummySMTP:
        def __init__(self, host, port, timeout):
            assert host == "smtp.example.com"
            assert int(port) == 587
            assert timeout == 10.0

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            return None

        def login(self, username, password):
            assert username == "user@example.com"
            assert password == "secret"

        def send_message(self, message):
            sent["called"] = True
            sent["subject"] = message["Subject"]
            sent["body"] = message.get_content()

    monkeypatch.setattr("app.slices.email.service.smtplib.SMTP", DummySMTP)

    response = client.post(
        "/email/send",
        headers=headers,
        json={
            "to_email": "team@example.com",
            "template_name": "welcome",
            "template_data": {
                "username": "Mailer",
                "login_url": "https://example.com/login",
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Email sent"
    assert sent["called"] is True
    assert sent["subject"] == "Welcome to Task Management API"
    assert "https://example.com/login" in sent["body"]


def test_send_email_retries_on_transient_smtp_error(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _auth_headers(client)

    os.environ["SMTP_HOST"] = "smtp.example.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["SMTP_USE_TLS"] = "true"
    os.environ["SMTP_USE_SSL"] = "false"
    os.environ["SMTP_USERNAME"] = "user@example.com"
    os.environ["SMTP_PASSWORD"] = "secret"
    os.environ["SMTP_FROM_EMAIL"] = "noreply@example.com"
    os.environ["SMTP_MAX_RETRIES"] = "2"
    os.environ["SMTP_RETRY_BACKOFF_SECONDS"] = "0.01"

    attempts = {"count": 0}
    sleeps = []

    class FlakySMTP:
        def __init__(self, host, port, timeout):
            del host, port, timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            return None

        def login(self, username, password):
            del username, password

        def send_message(self, message):
            del message
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise smtplib.SMTPServerDisconnected("temporary")

    def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr("app.slices.email.service.smtplib.SMTP", FlakySMTP)
    monkeypatch.setattr("app.slices.email.service.time.sleep", fake_sleep)

    response = client.post(
        "/email/send",
        headers=headers,
        json={"to_email": "team@example.com", "subject": "Retry", "body": "Works"},
    )

    assert response.status_code == 200
    assert attempts["count"] == 3
    assert sleeps == [0.01, 0.02]


def test_send_email_returns_503_for_missing_template_field(monkeypatch) -> None:
    _reset_db()
    client = TestClient(app)
    headers = _auth_headers(client)

    os.environ["SMTP_HOST"] = "smtp.example.com"
    os.environ["SMTP_FROM_EMAIL"] = "noreply@example.com"

    class DummySMTP:
        def __init__(self, host, port, timeout):
            del host, port, timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def send_message(self, message):
            del message

    monkeypatch.setattr("app.slices.email.service.smtplib.SMTP", DummySMTP)

    response = client.post(
        "/email/send",
        headers=headers,
        json={
            "to_email": "team@example.com",
            "template_name": "password_reset",
            "template_data": {"username": "Mailer"},
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Email service is not configured"


def test_send_email_returns_503_when_not_configured() -> None:
    _reset_db()
    client = TestClient(app)
    headers = _auth_headers(client)

    for key in (
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USE_TLS",
        "SMTP_USE_SSL",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_FROM_NAME",
    ):
        os.environ.pop(key, None)

    response = client.post(
        "/email/send",
        headers=headers,
        json={"to_email": "team@example.com", "subject": "Missing config", "body": "test"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Email service is not configured"
