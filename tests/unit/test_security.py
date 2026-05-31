import pytest

from app.core import security as security_module
from app.core.security import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def test_hash_password_and_verify_roundtrip() -> None:
    password = "strong-password-123"

    password_hash = hash_password(password)

    assert isinstance(password_hash, str)
    assert password_hash
    assert verify_password(password, password_hash) is True


def test_hash_password_uses_random_salt() -> None:
    password = "same-password"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_verify_password_returns_false_for_invalid_base64() -> None:
    assert verify_password("password", "not-base64-$$$") is False


def test_verify_password_returns_false_for_short_decoded_value() -> None:
    assert verify_password("password", "YQ==") is False


def test_verify_password_returns_false_for_wrong_password() -> None:
    password_hash = hash_password("correct-password")

    assert verify_password("wrong-password", password_hash) is False


def test_decode_access_token_roundtrip() -> None:
    token = create_access_token({"sub": "1", "username": "alice"})

    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["username"] == "alice"
    assert payload["token_use"] == "access"
    assert "iat" in payload
    assert "exp" in payload
    assert "jti" in payload


def test_decode_refresh_token_roundtrip() -> None:
    token = create_refresh_token({"sub": "1", "username": "alice"})

    payload = decode_refresh_token(token)

    assert payload["sub"] == "1"
    assert payload["username"] == "alice"
    assert payload["token_use"] == "refresh"
    assert "iat" in payload
    assert "exp" in payload
    assert "jti" in payload


def test_decode_access_token_rejects_refresh_token() -> None:
    refresh_token = create_refresh_token({"sub": "1", "username": "alice"})

    with pytest.raises(TokenDecodeError):
        decode_access_token(refresh_token)


def test_decode_refresh_token_rejects_access_token() -> None:
    access_token = create_access_token({"sub": "1", "username": "alice"})

    with pytest.raises(TokenDecodeError):
        decode_refresh_token(access_token)


def test_decode_access_token_rejects_invalid_token(mocker) -> None:
    mocker.patch(
        "app.core.security.jwt.decode",
        side_effect=security_module.InvalidTokenError("invalid"),
    )

    with pytest.raises(TokenDecodeError, match="Invalid authentication token"):
        decode_access_token("bad-token")


def test_decode_refresh_token_rejects_invalid_token(mocker) -> None:
    mocker.patch(
        "app.core.security.jwt.decode",
        side_effect=security_module.InvalidTokenError("invalid"),
    )

    with pytest.raises(TokenDecodeError, match="Invalid refresh token"):
        decode_refresh_token("bad-token")
