import logging
from uuid import uuid4
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True, trace_enabled: bool = False) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._trace_enabled = trace_enabled
        self._logger = logging.getLogger("app.request")

    @staticmethod
    def _trace_id_from_headers(request: Request) -> str | None:
        traceparent = request.headers.get("traceparent", "").strip()
        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 4 and len(parts[1]) == 32:
                return parts[1]

        trace_id = request.headers.get("x-trace-id", "").strip()
        return trace_id or None

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled:
            return await call_next(request)

        request_id = request.headers.get("x-request-id", "").strip() or uuid4().hex
        trace_id = self._trace_id_from_headers(request) if self._trace_enabled else None
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        start_time = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - start_time) * 1000
            client_host = request.client.host if request.client else "unknown"
            self._logger.exception(
                "%s %s failed after %.2fms client=%s request_id=%s%s",
                request.method,
                request.url.path,
                duration_ms,
                client_host,
                request_id,
                f" trace_id={trace_id}" if trace_id else "",
                extra={
                    "event": "http_request_failed",
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_host,
                },
            )
            raise

        duration_ms = (perf_counter() - start_time) * 1000
        client_host = request.client.host if request.client else "unknown"
        response.headers["X-Request-ID"] = request_id
        self._logger.info(
            "%s %s -> %s in %.2fms client=%s request_id=%s%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_host,
            request_id,
            f" trace_id={trace_id}" if trace_id else "",
            extra={
                "event": "http_request_completed",
                "request_id": request_id,
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_host,
            },
        )
        return response
