from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        enabled: bool = True,
        hsts_enabled: bool = True,
        frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str = "camera=(), microphone=(), geolocation=()",
        csp: str = "default-src 'self'; frame-ancestors 'none'",
    ) -> None:
        super().__init__(app)
        self._enabled = enabled
        self._hsts_enabled = hsts_enabled
        self._frame_options = frame_options
        self._referrer_policy = referrer_policy
        self._permissions_policy = permissions_policy
        self._csp = csp

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if not self._enabled:
            return response

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", self._frame_options)
        response.headers.setdefault("Referrer-Policy", self._referrer_policy)
        response.headers.setdefault("Permissions-Policy", self._permissions_policy)
        response.headers.setdefault("Content-Security-Policy", self._csp)

        if self._hsts_enabled and request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )

        return response
