import pytest

from app.core.security import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


def test_decode_access_token_rejects_refresh_token() -> None:
    refresh_token = create_refresh_token({"sub": "1", "username": "alice"})

    with pytest.raises(TokenDecodeError):
        decode_access_token(refresh_token)


def test_decode_refresh_token_rejects_access_token() -> None:
    access_token = create_access_token({"sub": "1", "username": "alice"})

    with pytest.raises(TokenDecodeError):
        decode_refresh_token(access_token)
