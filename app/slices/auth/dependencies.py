from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.models import User
from app.core.security import TokenDecodeError, decode_access_token
from app.slices.auth.repository import RefreshTokenRepository, UserRepository
from app.slices.auth.service import AuthService

_bearer = HTTPBearer(auto_error=False)
_repository = UserRepository()
_refresh_token_repository = RefreshTokenRepository()
_service = AuthService(_repository, _refresh_token_repository)


def get_auth_service() -> AuthService:
    return _service


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", "0"))
    except (TokenDecodeError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user


def get_request_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None:
        return User(id=0, username="anonymous", password_hash="")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload.get("sub", "0"))
    except (TokenDecodeError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user
