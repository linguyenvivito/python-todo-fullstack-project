from typing import Optional

from app.core.models import User
from app.core.security import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.slices.auth.repository import UserRepository


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

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
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> tuple[str, User]:
        try:
            payload = decode_refresh_token(refresh_token)
            user_id = int(payload.get("sub", "0"))
        except (TokenDecodeError, ValueError, TypeError) as exc:
            raise InvalidRefreshTokenError("Invalid refresh token") from exc

        user = self.get_user_by_id(user_id)
        if user is None:
            raise InvalidRefreshTokenError("Invalid refresh token")

        return create_access_token({"sub": str(user.id), "username": user.username}), user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self._repository.get_by_id(user_id)
