import smtplib

import pytest

from app.slices.email.service import (
    EmailConfigurationError,
    EmailDeliveryError,
    EmailService,
)


def test_get_required_env_returns_stripped_value(monkeypatch) -> None:
    monkeypatch.setenv("SMTP_HOST", " smtp.example.com ")

    assert EmailService._get_required_env("SMTP_HOST") == "smtp.example.com"


def test_get_required_env_raises_for_missing_value(monkeypatch) -> None:
    monkeypatch.delenv("SMTP_HOST", raising=False)

    with pytest.raises(EmailConfigurationError, match="SMTP_HOST"):
        EmailService._get_required_env("SMTP_HOST")


def test_render_template_welcome_requires_login_url() -> None:
    service = EmailService()

    with pytest.raises(EmailConfigurationError, match="login_url"):
        service._render_template("welcome", {"username": "alice"})


def test_render_template_password_reset_uses_defaults() -> None:
    service = EmailService()

    subject, body = service._render_template(
        "password_reset",
        {"username": "alice", "reset_link": "https://example.com/reset"},
    )

    assert subject == "Reset your password"
    assert "alice" in body
    assert "https://example.com/reset" in body
    assert "30 minutes" in body


def test_build_message_uses_plain_from_when_name_empty() -> None:
    service = EmailService()

    message = service._build_message(
        from_name="",
        from_email="noreply@example.com",
        to_email="team@example.com",
        subject="Hello",
        body="World",
    )

    assert message["From"] == "noreply@example.com"
    assert message["To"] == "team@example.com"
    assert message["Subject"] == "Hello"


def test_send_with_retry_retries_and_raises(monkeypatch, mocker) -> None:
    service = EmailService()
    monkeypatch.setenv("SMTP_MAX_RETRIES", "1")
    monkeypatch.setenv("SMTP_RETRY_BACKOFF_SECONDS", "0.01")
    sleep = mocker.patch("app.slices.email.service.time.sleep")

    class AlwaysFailSMTP:
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
            raise smtplib.SMTPServerDisconnected("temporary")

    with pytest.raises(EmailDeliveryError):
        service._send_with_retry(
            smtp_cls=AlwaysFailSMTP,
            smtp_host="smtp.example.com",
            smtp_port=587,
            timeout=10.0,
            smtp_use_tls=True,
            smtp_use_ssl=False,
            smtp_username="user@example.com",
            smtp_password="secret",
            message=service._build_message(
                from_name="Task API",
                from_email="noreply@example.com",
                to_email="team@example.com",
                subject="Hello",
                body="World",
            ),
        )

    sleep.assert_called_once_with(0.01)


def test_send_email_uses_ssl_transport_and_template(monkeypatch, mocker) -> None:
    service = EmailService()
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USE_TLS", "false")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "noreply@example.com")
    monkeypatch.setenv("SMTP_FROM_NAME", "Task API")
    monkeypatch.setenv("SMTP_TIMEOUT", "8")

    render = mocker.patch.object(service, "_render_template", return_value=("Subj", "Body"))
    send = mocker.patch.object(service, "_send_with_retry")
    smtp_ssl_cls = mocker.patch("app.slices.email.service.smtplib.SMTP_SSL")

    service.send_email(
        to_email="team@example.com",
        template_name="welcome",
        template_data={"username": "alice", "login_url": "https://example.com/login"},
    )

    render.assert_called_once_with(
        "welcome", {"username": "alice", "login_url": "https://example.com/login"}
    )
    assert send.call_args.kwargs["smtp_cls"] == smtp_ssl_cls
    assert send.call_args.kwargs["smtp_host"] == "smtp.example.com"
    assert send.call_args.kwargs["smtp_port"] == 465
    assert send.call_args.kwargs["timeout"] == 8.0


def test_send_email_requires_from_email_or_username(monkeypatch) -> None:
    service = EmailService()
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.delenv("SMTP_FROM_EMAIL", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)

    with pytest.raises(EmailConfigurationError, match="SMTP_FROM_EMAIL"):
        service.send_email(
            to_email="team@example.com",
            subject="Hello",
            body="World",
        )
