from unittest.mock import Mock

import pytest

from app.core.models import User
from app.slices.auth.service import AuthService, InvalidRefreshTokenError


def test_create_token_pair_for_user_returns_two_tokens() -> None:
    repository = Mock()
    service = AuthService(repository)
    user = User(id=1, username="alice", password_hash="hash")

    access_token, refresh_token = service.create_token_pair_for_user(user)

    assert isinstance(access_token, str) and access_token
    assert isinstance(refresh_token, str) and refresh_token
    assert access_token != refresh_token


def test_refresh_access_token_returns_new_access_token_and_user() -> None:
    repository = Mock()
    user = User(id=7, username="alice", password_hash="hash")
    repository.get_by_id.return_value = user
    service = AuthService(repository)

    _, refresh_token = service.create_token_pair_for_user(user)
    access_token, resolved_user = service.refresh_access_token(refresh_token)

    assert isinstance(access_token, str) and access_token
    assert resolved_user.id == 7


def test_refresh_access_token_raises_for_invalid_token() -> None:
    repository = Mock()
    service = AuthService(repository)

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh_access_token("invalid-token")


def test_refresh_access_token_raises_for_deleted_user() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None
    service = AuthService(repository)
    user = User(id=33, username="bob", password_hash="hash")
    _, refresh_token = service.create_token_pair_for_user(user)

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh_access_token(refresh_token)
