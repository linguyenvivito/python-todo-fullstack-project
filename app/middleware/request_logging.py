import logging
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._logger = logging.getLogger("app.request")

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled:
            return await call_next(request)

        start_time = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - start_time) * 1000
            client_host = request.client.host if request.client else "unknown"
            self._logger.exception(
                "%s %s failed after %.2fms client=%s",
                request.method,
                request.url.path,
                duration_ms,
                client_host,
            )
            raise

        duration_ms = (perf_counter() - start_time) * 1000
        client_host = request.client.host if request.client else "unknown"
        self._logger.info(
            "%s %s -> %s in %.2fms client=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_host,
        )
        return response
