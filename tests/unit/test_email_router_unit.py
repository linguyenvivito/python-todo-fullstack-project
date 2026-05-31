import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.models import User
from app.slices.email import router as email_router
from app.slices.email.models import SendEmailRequest
from app.slices.email.service import EmailConfigurationError, EmailDeliveryError


def _request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/email/send",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "http_version": "1.1",
    }
    return Request(scope)


def test_list_email_templates_maps_response_model() -> None:
    class FakeEmailService:
        def list_templates(self):
            return [
                {
                    "name": "welcome",
                    "display_name": "Welcome",
                    "description": "Greets users",
                    "fields": [
                        {
                            "name": "username",
                            "label": "Username",
                            "required": True,
                            "placeholder": "alice",
                        }
                    ],
                }
            ]

    response = email_router.list_email_templates(
        email_service=FakeEmailService(),
        current_user=User(id=1, username="alice", password_hash="hash"),
    )

    assert len(response.items) == 1
    assert response.items[0].name == "welcome"
    assert response.items[0].fields[0].name == "username"


def test_send_email_success_returns_ok_and_audits(mocker) -> None:
    request = _request()
    payload = SendEmailRequest(
        to_email="team@example.com",
        subject="Hello",
        body="World",
    )
    service = mocker.Mock()
    current_user = User(id=7, username="alice", password_hash="hash")
    record_event = mocker.patch.object(email_router.audit_service, "record_event")

    response = email_router.send_email(
        request=request,
        payload=payload,
        email_service=service,
        current_user=current_user,
    )

    assert response.detail == "Email sent"
    assert record_event.call_args.kwargs["success"] is True
    assert record_event.call_args.kwargs["status_code"] == 200


def test_send_email_maps_configuration_error_to_503(mocker) -> None:
    request = _request()
    payload = SendEmailRequest(
        to_email="team@example.com",
        subject="Hello",
        body="World",
    )
    service = mocker.Mock()
    service.send_email.side_effect = EmailConfigurationError("missing")
    current_user = User(id=7, username="alice", password_hash="hash")
    record_event = mocker.patch.object(email_router.audit_service, "record_event")

    with pytest.raises(HTTPException) as exc_info:
        email_router.send_email(
            request=request,
            payload=payload,
            email_service=service,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Email service is not configured"
    assert record_event.call_args.kwargs["success"] is False
    assert record_event.call_args.kwargs["status_code"] == 503


def test_send_email_maps_delivery_error_to_502(mocker) -> None:
    request = _request()
    payload = SendEmailRequest(
        to_email="team@example.com",
        subject="Hello",
        body="World",
    )
    service = mocker.Mock()
    service.send_email.side_effect = EmailDeliveryError("failed")
    current_user = User(id=7, username="alice", password_hash="hash")
    record_event = mocker.patch.object(email_router.audit_service, "record_event")

    with pytest.raises(HTTPException) as exc_info:
        email_router.send_email(
            request=request,
            payload=payload,
            email_service=service,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "Failed to send email"
    assert record_event.call_args.kwargs["success"] is False
    assert record_event.call_args.kwargs["status_code"] == 502
