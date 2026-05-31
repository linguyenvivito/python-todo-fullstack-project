import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.audit import audit_service
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
logger = logging.getLogger("app.api.auth")


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
        audit_service.record_event(
            action="auth.register",
            success=False,
            request=request,
            status_code=status.HTTP_409_CONFLICT,
            details={"reason": "user_already_exists", "username": payload.username},
        )
        logger.warning("register conflict username=%s", payload.username)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    audit_service.record_event(
        action="auth.register",
        success=True,
        request=request,
        actor_user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        status_code=status.HTTP_201_CREATED,
    )
    logger.info("register success user_id=%s username=%s", user.id, user.username)
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
        audit_service.record_event(
            action="auth.login",
            success=False,
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"reason": "invalid_credentials", "username": payload.username},
        )
        logger.warning("login failed username=%s", payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    access_token, refresh_token = auth_service.create_token_pair_for_user(user)
    audit_service.record_event(
        action="auth.login",
        success=True,
        request=request,
        actor_user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        status_code=status.HTTP_200_OK,
    )
    logger.info("login success user_id=%s username=%s", user.id, user.username)
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
        audit_service.record_event(
            action="auth.refresh",
            success=False,
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"reason": "invalid_refresh_token"},
        )
        logger.warning("refresh failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    audit_service.record_event(
        action="auth.refresh",
        success=True,
        request=request,
        actor_user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        status_code=status.HTTP_200_OK,
    )
    logger.info("refresh success user_id=%s username=%s", user.id, user.username)
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
        audit_service.record_event(
            action="auth.revoke",
            success=False,
            request=request,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details={"reason": "invalid_refresh_token"},
        )
        logger.warning("revoke failed")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    audit_service.record_event(
        action="auth.revoke",
        success=True,
        request=request,
        status_code=status.HTTP_204_NO_CONTENT,
    )
    logger.info("revoke success")
