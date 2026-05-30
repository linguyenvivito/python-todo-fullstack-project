import os
from typing import Callable

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for

    explicit_client_id = request.headers.get("x-client-id", "").strip()
    if explicit_client_id:
        return explicit_client_id

    return get_remote_address(request)


def is_rate_limiting_enabled() -> bool:
    return os.getenv("RATE_LIMITING_ENABLED", "true").strip().lower() == "true"


def rate_limit(env_var_name: str, default_value: str) -> Callable[[], str]:
    def _resolve_limit() -> str:
        if not is_rate_limiting_enabled():
            return "1000000/minute"
        return os.getenv(env_var_name, default_value).strip()

    return _resolve_limit


limiter = Limiter(key_func=_client_identifier)
