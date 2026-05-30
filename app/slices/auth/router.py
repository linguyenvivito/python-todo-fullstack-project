from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import limiter, rate_limit
from app.slices.auth.dependencies import get_auth_service
from app.slices.auth.models import (
    LoginRequest,
    RefreshTokenRequest,
    RevokeTokenRequest,
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
@limiter.limit(rate_limit("RATE_LIMIT_AUTH_REGISTER", "30/minute"))
def register_user(
    request: Request,
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    try:
        user = auth_service.register_user(payload.username, payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    return UserResponse(id=user.id, username=user.username)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(rate_limit("RATE_LIMIT_AUTH_LOGIN", "30/minute"))
def login(
    request: Request,
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
@limiter.limit(rate_limit("RATE_LIMIT_AUTH_REFRESH", "120/minute"))
def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        access_token, rotated_refresh_token, user = auth_service.refresh_access_token(
            payload.refresh_token
        )
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return TokenResponse(
        access_token=access_token,
        refresh_token=rotated_refresh_token,
        user=UserResponse(id=user.id, username=user.username),
    )


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_limit("RATE_LIMIT_AUTH_REVOKE", "60/minute"))
def revoke_token(
    request: Request,
    payload: RevokeTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    try:
        auth_service.revoke_refresh_token(payload.refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
