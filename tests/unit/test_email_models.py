import pytest
from pydantic import ValidationError

from app.slices.email.models import SendEmailRequest


def test_send_email_request_sanitizes_email_and_text_fields() -> None:
    payload = SendEmailRequest(
        to_email="  <b>USER@Example.com</b>  ",
        subject=" <i>Hello</i> ",
        body=" <script>x</script>Body ",
    )

    assert payload.to_email == "user@example.com"
    assert payload.subject == "Hello"
    assert payload.body == "xBody"


def test_send_email_request_sanitizes_template_fields() -> None:
    payload = SendEmailRequest(
        to_email="team@example.com",
        template_name=" <b>WELCOME</b> ",
        template_data={" <i>user</i> ": " <script>Alice</script> ", "empty": None},
    )

    assert payload.template_name == "welcome"
    assert payload.template_data == {"user": "Alice", "empty": ""}


def test_send_email_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError, match="Invalid recipient email"):
        SendEmailRequest(
            to_email="invalid-email",
            subject="hello",
            body="world",
        )


def test_send_email_request_requires_exactly_one_content_source() -> None:
    with pytest.raises(ValidationError, match="Provide either subject/body or template_name"):
        SendEmailRequest(to_email="team@example.com")

    with pytest.raises(ValidationError, match="Provide either subject/body or template_name"):
        SendEmailRequest(
            to_email="team@example.com",
            subject="hello",
            body="world",
            template_name="welcome",
            template_data={"username": "Alice", "login_url": "https://example.com/login"},
        )
