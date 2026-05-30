import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.rate_limit import limiter
from app.middleware.cors_restriction import CorsRestrictionMiddleware
from app.middleware.csrf_protection import CsrfProtectionMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.slices.auth.router import router as auth_router
from app.slices.tasks.router import router as tasks_router


def create_app() -> FastAPI:
    app = FastAPI(title="Task Management API")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.get("/health")
    def health_check() -> Dict[str, str]:
        return {"status": "ok"}

    cors_allow_origins = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://127.0.0.1:8880,http://localhost:8880,http://127.0.0.1:5173,http://localhost:5173",
    )
    allow_origins = [origin.strip() for origin in cors_allow_origins.split(",") if origin.strip()]

    csrf_trusted_origins = os.getenv("CSRF_TRUSTED_ORIGINS", cors_allow_origins)
    trusted_origins = [origin.strip() for origin in csrf_trusted_origins.split(",") if origin.strip()]

    csrf_enabled = os.getenv("CSRF_ENABLED", "true").strip().lower() == "true"
    csrf_cookie_based_only = (
        os.getenv("CSRF_COOKIE_BASED_ONLY", "true").strip().lower() == "true"
    )
    security_headers_enabled = (
        os.getenv("SECURITY_HEADERS_ENABLED", "true").strip().lower() == "true"
    )
    security_hsts_enabled = (
        os.getenv("SECURITY_HSTS_ENABLED", "true").strip().lower() == "true"
    )
    strict_origin_check = os.getenv("CORS_STRICT_ORIGIN_CHECK", "true").strip().lower() == "true"

    app.add_middleware(
        SecurityHeadersMiddleware,
        enabled=security_headers_enabled,
        hsts_enabled=security_hsts_enabled,
    )

    app.add_middleware(
        CsrfProtectionMiddleware,
        trusted_origins=trusted_origins,
        enabled=csrf_enabled,
        cookie_based_only=csrf_cookie_based_only,
    )

    app.add_middleware(
        CorsRestrictionMiddleware,
        allow_origins=allow_origins,
        strict=strict_origin_check,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SlowAPIMiddleware)
    app.include_router(auth_router)
    app.include_router(tasks_router)
    return app


app = create_app()
