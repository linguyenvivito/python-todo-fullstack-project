from typing import Iterable, Set
from urllib.parse import urlparse

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    _UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(
        self,
        app,
        trusted_origins: Iterable[str],
        enabled: bool = True,
        cookie_based_only: bool = True,
    ) -> None:
        super().__init__(app)
        self._trusted_origins: Set[str] = {
            origin.strip() for origin in trusted_origins if origin.strip()
        }
        self._enabled = enabled
        self._cookie_based_only = cookie_based_only

    @staticmethod
    def _origin_from_referer(referer: str) -> str:
        parsed = urlparse(referer)
        if not parsed.scheme or not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def _request_origin(request: Request) -> str:
        return f"{request.url.scheme}://{request.url.netloc}"

    def _is_trusted_origin(self, candidate_origin: str, request: Request) -> bool:
        return (
            candidate_origin in self._trusted_origins
            or candidate_origin == self._request_origin(request)
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._enabled or request.method.upper() not in self._UNSAFE_METHODS:
            return await call_next(request)

        if self._cookie_based_only and "cookie" not in request.headers:
            return await call_next(request)

        origin = request.headers.get("origin", "").strip()
        if origin:
            if self._is_trusted_origin(origin, request):
                return await call_next(request)
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        referer = request.headers.get("referer", "").strip()
        if referer:
            referer_origin = self._origin_from_referer(referer)
            if referer_origin and self._is_trusted_origin(referer_origin, request):
                return await call_next(request)
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF validation failed: missing origin"},
        )
