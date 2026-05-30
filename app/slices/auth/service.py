import time
from typing import Any, Optional

from app.core.models import User
from app.core.security import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.slices.auth.repository import RefreshTokenRepository, UserRepository


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class AuthService:
    def __init__(self, repository: UserRepository, refresh_token_repository: RefreshTokenRepository) -> None:
        self._repository = repository
        self._refresh_token_repository = refresh_token_repository

    @staticmethod
    def _to_int(value: Any) -> int:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            return int(value)
        raise ValueError("Unsupported numeric claim type")

    def register_user(self, username: str, password: str) -> User:
        normalized_username = username.strip().lower()
        if self._repository.get_by_username(normalized_username) is not None:
            raise UserAlreadyExistsError("Username is already in use")

        password_hash = hash_password(password)
        return self._repository.create(normalized_username, password_hash)

    def authenticate(self, username: str, password: str) -> User:
        normalized_username = username.strip().lower()
        user = self._repository.get_by_username(normalized_username)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password")
        return user

    def create_token_for_user(self, user: User) -> str:
        return create_access_token({"sub": str(user.id), "username": user.username})

    def create_token_pair_for_user(self, user: User) -> tuple[str, str]:
        token_payload = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)
        refresh_payload = decode_refresh_token(refresh_token)
        refresh_jti = str(refresh_payload.get("jti", ""))
        refresh_exp = self._to_int(refresh_payload.get("exp", 0))
        if not refresh_jti or refresh_exp <= 0:
            raise RuntimeError("Failed to issue refresh token metadata")

        self._refresh_token_repository.store(refresh_jti, user.id, refresh_exp)
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[str, str, User]:
        try:
            payload = decode_refresh_token(refresh_token)
            user_id = int(payload.get("sub", "0"))
            token_jti = str(payload.get("jti", ""))
        except (TokenDecodeError, ValueError, TypeError) as exc:
            raise InvalidRefreshTokenError("Invalid refresh token") from exc

        if not token_jti:
            raise InvalidRefreshTokenError("Invalid refresh token")

        token_record = self._refresh_token_repository.get(token_jti)
        if token_record is None or token_record.user_id != user_id:
            raise InvalidRefreshTokenError("Invalid refresh token")

        now_ts = int(time.time())
        if token_record.revoked_at is not None:
            self._refresh_token_repository.revoke_all_for_user(user_id, revoked_at=now_ts)
            raise InvalidRefreshTokenError("Invalid refresh token")

        if token_record.expires_at <= now_ts:
            self._refresh_token_repository.revoke(token_jti, revoked_at=now_ts)
            raise InvalidRefreshTokenError("Invalid refresh token")

        user = self.get_user_by_id(user_id)
        if user is None:
            self._refresh_token_repository.revoke(token_jti, revoked_at=now_ts)
            raise InvalidRefreshTokenError("Invalid refresh token")

        access_token, rotated_refresh_token = self.create_token_pair_for_user(user)
        rotated_payload = decode_refresh_token(rotated_refresh_token)
        rotated_jti = str(rotated_payload.get("jti", ""))
        self._refresh_token_repository.revoke(
            token_jti,
            revoked_at=now_ts,
            replaced_by_jti=rotated_jti if rotated_jti else None,
        )
        return access_token, rotated_refresh_token, user

    def revoke_refresh_token(self, refresh_token: str) -> None:
        try:
            payload = decode_refresh_token(refresh_token)
            user_id = int(payload.get("sub", "0"))
            token_jti = str(payload.get("jti", ""))
        except (TokenDecodeError, ValueError, TypeError) as exc:
            raise InvalidRefreshTokenError("Invalid refresh token") from exc

        if not token_jti:
            raise InvalidRefreshTokenError("Invalid refresh token")

        token_record = self._refresh_token_repository.get(token_jti)
        if token_record is None or token_record.user_id != user_id:
            raise InvalidRefreshTokenError("Invalid refresh token")

        self._refresh_token_repository.revoke(token_jti, revoked_at=int(time.time()))

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self._repository.get_by_id(user_id)
