import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.models import User
from app.core.security import TokenDecodeError
from app.slices.auth import dependencies as auth_dependencies


def test_get_auth_service_is_cached(mocker) -> None:
    auth_dependencies.get_auth_service.cache_clear()

    user_repo = object()
    refresh_repo = object()
    mocker.patch("app.slices.auth.dependencies.UserRepository", return_value=user_repo)
    mocker.patch(
        "app.slices.auth.dependencies.RefreshTokenRepository", return_value=refresh_repo
    )
    service_cls = mocker.patch("app.slices.auth.dependencies.AuthService")

    first = auth_dependencies.get_auth_service()
    second = auth_dependencies.get_auth_service()

    assert first is second
    service_cls.assert_called_once_with(user_repo, refresh_repo)


def test_get_current_user_requires_credentials() -> None:
    fake_auth_service = object()

    with pytest.raises(HTTPException, match="Missing authentication token") as exc_info:
        auth_dependencies.get_current_user(None, fake_auth_service)

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_invalid_token(mocker) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    fake_auth_service = object()
    mocker.patch(
        "app.slices.auth.dependencies.decode_access_token",
        side_effect=TokenDecodeError("invalid"),
    )

    with pytest.raises(HTTPException, match="Invalid authentication token") as exc_info:
        auth_dependencies.get_current_user(credentials, fake_auth_service)

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_missing_user(mocker) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    auth_service = mocker.Mock()
    auth_service.get_user_by_id.return_value = None
    mocker.patch("app.slices.auth.dependencies.decode_access_token", return_value={"sub": "9"})

    with pytest.raises(HTTPException, match="User no longer exists") as exc_info:
        auth_dependencies.get_current_user(credentials, auth_service)

    assert exc_info.value.status_code == 401


def test_get_current_user_returns_user_on_valid_token(mocker) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    expected_user = User(id=7, username="alice", password_hash="hash")
    auth_service = mocker.Mock()
    auth_service.get_user_by_id.return_value = expected_user
    mocker.patch("app.slices.auth.dependencies.decode_access_token", return_value={"sub": "7"})

    user = auth_dependencies.get_current_user(credentials, auth_service)

    assert user == expected_user


def test_get_request_user_returns_anonymous_without_credentials() -> None:
    fake_auth_service = object()

    user = auth_dependencies.get_request_user(None, fake_auth_service)

    assert user.id == 0
    assert user.username == "anonymous"


def test_get_request_user_rejects_invalid_token(mocker) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad-token")
    fake_auth_service = object()
    mocker.patch(
        "app.slices.auth.dependencies.decode_access_token",
        side_effect=TokenDecodeError("invalid"),
    )

    with pytest.raises(HTTPException, match="Invalid authentication token") as exc_info:
        auth_dependencies.get_request_user(credentials, fake_auth_service)

    assert exc_info.value.status_code == 401


def test_get_request_user_rejects_missing_user(mocker) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    auth_service = mocker.Mock()
    auth_service.get_user_by_id.return_value = None
    mocker.patch("app.slices.auth.dependencies.decode_access_token", return_value={"sub": "9"})

    with pytest.raises(HTTPException, match="User no longer exists") as exc_info:
        auth_dependencies.get_request_user(credentials, auth_service)

    assert exc_info.value.status_code == 401


def test_get_request_user_returns_user_on_valid_token(mocker) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    expected_user = User(id=11, username="bob", password_hash="hash")
    auth_service = mocker.Mock()
    auth_service.get_user_by_id.return_value = expected_user
    mocker.patch("app.slices.auth.dependencies.decode_access_token", return_value={"sub": "11"})

    user = auth_dependencies.get_request_user(credentials, auth_service)

    assert user == expected_user
