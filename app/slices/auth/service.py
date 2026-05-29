from typing import Optional

from app.core.models import User
from app.core.security import create_access_token, hash_password, verify_password
from app.slices.auth.repository import UserRepository


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
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

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self._repository.get_by_id(user_id)
