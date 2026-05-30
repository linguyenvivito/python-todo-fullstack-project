from unittest.mock import Mock

import pytest

from app.core.models import User
from app.slices.auth.service import AuthService, InvalidRefreshTokenError


def test_create_token_pair_for_user_returns_two_tokens() -> None:
    repository = Mock()
    refresh_token_repository = Mock()
    service = AuthService(repository, refresh_token_repository)
    user = User(id=1, username="alice", password_hash="hash")

    access_token, refresh_token = service.create_token_pair_for_user(user)

    assert isinstance(access_token, str) and access_token
    assert isinstance(refresh_token, str) and refresh_token
    assert access_token != refresh_token
    refresh_token_repository.store.assert_called_once()


def test_refresh_access_token_returns_new_access_token_and_user() -> None:
    repository = Mock()
    refresh_token_repository = Mock()
    user = User(id=7, username="alice", password_hash="hash")
    repository.get_by_id.return_value = user
    service = AuthService(repository, refresh_token_repository)

    _, refresh_token = service.create_token_pair_for_user(user)
    refresh_token_repository.get.return_value = Mock(
        user_id=7,
        expires_at=9_999_999_999,
        revoked_at=None,
    )
    access_token, rotated_refresh_token, resolved_user = service.refresh_access_token(refresh_token)

    assert isinstance(access_token, str) and access_token
    assert isinstance(rotated_refresh_token, str) and rotated_refresh_token
    assert resolved_user.id == 7
    refresh_token_repository.revoke.assert_called_once()


def test_refresh_access_token_raises_for_invalid_token() -> None:
    repository = Mock()
    refresh_token_repository = Mock()
    service = AuthService(repository, refresh_token_repository)

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh_access_token("invalid-token")


def test_refresh_access_token_raises_for_deleted_user() -> None:
    repository = Mock()
    refresh_token_repository = Mock()
    repository.get_by_id.return_value = None
    service = AuthService(repository, refresh_token_repository)
    user = User(id=33, username="bob", password_hash="hash")
    _, refresh_token = service.create_token_pair_for_user(user)
    refresh_token_repository.get.return_value = Mock(
        user_id=33,
        expires_at=9_999_999_999,
        revoked_at=None,
    )

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh_access_token(refresh_token)


def test_refresh_access_token_reuse_revokes_all_tokens_for_user() -> None:
    repository = Mock()
    refresh_token_repository = Mock()
    service = AuthService(repository, refresh_token_repository)
    user = User(id=2, username="eve", password_hash="hash")
    _, refresh_token = service.create_token_pair_for_user(user)

    refresh_token_repository.get.return_value = Mock(
        user_id=2,
        expires_at=9_999_999_999,
        revoked_at=123,
    )

    with pytest.raises(InvalidRefreshTokenError):
        service.refresh_access_token(refresh_token)

    refresh_token_repository.revoke_all_for_user.assert_called_once()


def test_revoke_refresh_token_marks_token_as_revoked() -> None:
    repository = Mock()
    refresh_token_repository = Mock()
    service = AuthService(repository, refresh_token_repository)
    user = User(id=55, username="mallory", password_hash="hash")
    _, refresh_token = service.create_token_pair_for_user(user)
    refresh_token_repository.get.return_value = Mock(user_id=55)

    service.revoke_refresh_token(refresh_token)

    refresh_token_repository.revoke.assert_called_once()
