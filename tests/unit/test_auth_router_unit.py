import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.models import User
from app.slices.auth import router as auth_router
from app.slices.auth.models import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RevokeTokenRequest,
)
from app.slices.auth.service import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)


def _request(path: str) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "http_version": "1.1",
    }
    return Request(scope)


def test_register_user_success_returns_user_response(mocker) -> None:
    request = _request("/auth/register")
    payload = RegisterRequest(username="Alice", password="password123")
    auth_service = mocker.Mock()
    auth_service.register_user.return_value = User(id=7, username="alice", password_hash="hash")
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    response = auth_router.register_user(
        request=request,
        payload=payload,
        auth_service=auth_service,
    )

    assert response.id == 7
    assert response.username == "alice"
    assert record_event.call_args.kwargs["action"] == "auth.register"
    assert record_event.call_args.kwargs["success"] is True
    assert record_event.call_args.kwargs["status_code"] == 201


def test_register_user_maps_already_exists_to_409(mocker) -> None:
    request = _request("/auth/register")
    payload = RegisterRequest(username="Alice", password="password123")
    auth_service = mocker.Mock()
    auth_service.register_user.side_effect = UserAlreadyExistsError("Username is already in use")
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    with pytest.raises(HTTPException) as exc_info:
        auth_router.register_user(
            request=request,
            payload=payload,
            auth_service=auth_service,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Username is already in use"
    assert record_event.call_args.kwargs["action"] == "auth.register"
    assert record_event.call_args.kwargs["success"] is False
    assert record_event.call_args.kwargs["status_code"] == 409


def test_login_success_returns_token_response(mocker) -> None:
    request = _request("/auth/login")
    payload = LoginRequest(username="Alice", password="password123")
    auth_service = mocker.Mock()
    user = User(id=9, username="alice", password_hash="hash")
    auth_service.authenticate.return_value = user
    auth_service.create_token_pair_for_user.return_value = ("access-token", "refresh-token")
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    response = auth_router.login(
        request=request,
        payload=payload,
        auth_service=auth_service,
    )

    assert response.access_token == "access-token"
    assert response.refresh_token == "refresh-token"
    assert response.user.id == 9
    assert response.user.username == "alice"
    assert record_event.call_args.kwargs["action"] == "auth.login"
    assert record_event.call_args.kwargs["success"] is True
    assert record_event.call_args.kwargs["status_code"] == 200


def test_login_maps_invalid_credentials_to_401(mocker) -> None:
    request = _request("/auth/login")
    payload = LoginRequest(username="Alice", password="password123")
    auth_service = mocker.Mock()
    auth_service.authenticate.side_effect = InvalidCredentialsError("Invalid username or password")
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    with pytest.raises(HTTPException) as exc_info:
        auth_router.login(
            request=request,
            payload=payload,
            auth_service=auth_service,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid username or password"
    assert record_event.call_args.kwargs["action"] == "auth.login"
    assert record_event.call_args.kwargs["success"] is False
    assert record_event.call_args.kwargs["status_code"] == 401


def test_refresh_token_success_returns_rotated_tokens(mocker) -> None:
    request = _request("/auth/refresh")
    payload = RefreshTokenRequest(refresh_token="refresh-token")
    auth_service = mocker.Mock()
    user = User(id=11, username="bob", password_hash="hash")
    auth_service.refresh_access_token.return_value = ("new-access", "new-refresh", user)
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    response = auth_router.refresh_token(
        request=request,
        payload=payload,
        auth_service=auth_service,
    )

    assert response.access_token == "new-access"
    assert response.refresh_token == "new-refresh"
    assert response.user.id == 11
    assert response.user.username == "bob"
    assert record_event.call_args.kwargs["action"] == "auth.refresh"
    assert record_event.call_args.kwargs["success"] is True
    assert record_event.call_args.kwargs["status_code"] == 200


def test_refresh_token_maps_invalid_refresh_to_401(mocker) -> None:
    request = _request("/auth/refresh")
    payload = RefreshTokenRequest(refresh_token="refresh-token")
    auth_service = mocker.Mock()
    auth_service.refresh_access_token.side_effect = InvalidRefreshTokenError("Invalid refresh token")
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    with pytest.raises(HTTPException) as exc_info:
        auth_router.refresh_token(
            request=request,
            payload=payload,
            auth_service=auth_service,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid refresh token"
    assert record_event.call_args.kwargs["action"] == "auth.refresh"
    assert record_event.call_args.kwargs["success"] is False
    assert record_event.call_args.kwargs["status_code"] == 401


def test_revoke_token_success_records_audit(mocker) -> None:
    request = _request("/auth/revoke")
    payload = RevokeTokenRequest(refresh_token="refresh-token")
    auth_service = mocker.Mock()
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    response = auth_router.revoke_token(
        request=request,
        payload=payload,
        auth_service=auth_service,
    )

    assert response is None
    auth_service.revoke_refresh_token.assert_called_once_with("refresh-token")
    assert record_event.call_args.kwargs["action"] == "auth.revoke"
    assert record_event.call_args.kwargs["success"] is True
    assert record_event.call_args.kwargs["status_code"] == 204


def test_revoke_token_maps_invalid_refresh_to_401(mocker) -> None:
    request = _request("/auth/revoke")
    payload = RevokeTokenRequest(refresh_token="refresh-token")
    auth_service = mocker.Mock()
    auth_service.revoke_refresh_token.side_effect = InvalidRefreshTokenError("Invalid refresh token")
    record_event = mocker.patch.object(auth_router.audit_service, "record_event")

    with pytest.raises(HTTPException) as exc_info:
        auth_router.revoke_token(
            request=request,
            payload=payload,
            auth_service=auth_service,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid refresh token"
    assert record_event.call_args.kwargs["action"] == "auth.revoke"
    assert record_event.call_args.kwargs["success"] is False
    assert record_event.call_args.kwargs["status_code"] == 401
