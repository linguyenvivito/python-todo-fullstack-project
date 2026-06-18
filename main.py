import os
import logging
from time import time
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.database import get_connection
from app.core.logging_config import configure_logging
from app.core.rate_limit import limiter
from app.middleware.cors_restriction import CorsRestrictionMiddleware
from app.middleware.csrf_protection import CsrfProtectionMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_metrics import RequestMetricsMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.slices.auth.router import router as auth_router
from app.slices.audit.router import router as audit_router
from app.slices.email.router import router as email_router
from app.slices.tasks.router import router as tasks_router
from app.slices.roles.router import router as roles_router
from app.slices.users.router import router as users_router

logger = logging.getLogger("app.security.rate_limit")
APP_STARTED_AT = time()


def _handle_rate_limit_exceeded(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RateLimitExceeded):
        client_host = request.client.host if request.client else "unknown"
        logger.warning(
            "rate limit exceeded method=%s path=%s client=%s",
            request.method,
            request.url.path,
            client_host,
        )
        return _rate_limit_exceeded_handler(request, exc)
    raise exc


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Task Management API")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _handle_rate_limit_exceeded)

    @app.get("/health")
    def health_check() -> Dict[str, Any]:
        return {
            "status": "ok",
            "uptime_seconds": int(max(0, time() - APP_STARTED_AT)),
        }

    @app.get("/ready")
    def readiness_check() -> JSONResponse:
        readiness_check_database = (
            os.getenv("READINESS_CHECK_DATABASE", "true").strip().lower() == "true"
        )

        checks: Dict[str, str] = {"database": "skipped"}
        status_code = 200

        if readiness_check_database:
            try:
                with get_connection() as connection:
                    cursor = connection.cursor()
                    try:
                        cursor.execute("SELECT 1")
                    finally:
                        cursor.close()
            except Exception:
                checks["database"] = "error"
                status_code = 503
            else:
                checks["database"] = "ok"

        payload = {
            "status": "ready" if status_code == 200 else "not_ready",
            "checks": checks,
        }
        return JSONResponse(content=payload, status_code=status_code)

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        metrics_enabled = os.getenv("METRICS_ENABLED", "true").strip().lower() == "true"
        if not metrics_enabled:
            return Response(status_code=404)
        return Response(content=generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)

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
    request_logging_enabled = (
        os.getenv("REQUEST_LOGGING_ENABLED", "true").strip().lower() == "true"
    )
    trace_enabled = os.getenv("TRACE_ENABLED", "false").strip().lower() == "true"
    metrics_enabled = os.getenv("METRICS_ENABLED", "true").strip().lower() == "true"
    strict_origin_check = os.getenv("CORS_STRICT_ORIGIN_CHECK", "true").strip().lower() == "true"

    app.add_middleware(
        RequestLoggingMiddleware,
        enabled=request_logging_enabled,
        trace_enabled=trace_enabled,
    )

    app.add_middleware(
        RequestMetricsMiddleware,
        enabled=metrics_enabled,
    )

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
    app.include_router(audit_router)
    app.include_router(email_router)
    app.include_router(tasks_router)
    app.include_router(roles_router)
    app.include_router(users_router)
    return app


app = create_app()
