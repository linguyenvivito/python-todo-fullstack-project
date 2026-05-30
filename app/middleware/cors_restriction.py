from typing import Iterable, Set

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorsRestrictionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allow_origins: Iterable[str], strict: bool = True) -> None:
        super().__init__(app)
        self._allow_origins: Set[str] = {origin.strip() for origin in allow_origins if origin.strip()}
        self._strict = strict

    def _is_same_origin(self, origin: str, request: Request) -> bool:
        request_origin = f"{request.url.scheme}://{request.url.netloc}"
        return origin == request_origin

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self._strict:
            return await call_next(request)

        origin = request.headers.get("origin", "").strip()
        if not origin:
            return await call_next(request)

        if origin in self._allow_origins or self._is_same_origin(origin, request):
            return await call_next(request)

        return JSONResponse(
            status_code=403,
            content={"detail": "Origin is not allowed"},
        )
