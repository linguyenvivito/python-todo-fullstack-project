from fastapi import APIRouter, Depends, HTTPException, status

from app.slices.auth.dependencies import get_auth_service
from app.slices.auth.models import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.slices.auth.service import (
    AuthService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserAlreadyExistsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        user = auth_service.register_user(payload.username, payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return UserResponse(id=user.id, username=user.username)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        user = auth_service.authenticate(payload.username, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    access_token, refresh_token = auth_service.create_token_pair_for_user(user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(id=user.id, username=user.username),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access_token, user = auth_service.refresh_access_token(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return TokenResponse(
        access_token=access_token,
        refresh_token=payload.refresh_token,
        user=UserResponse(id=user.id, username=user.username),
    )
