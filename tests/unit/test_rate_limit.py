from starlette.requests import Request

from app.core.rate_limit import _client_identifier, is_rate_limiting_enabled, rate_limit


def _build_request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (name.lower().encode("utf-8"), value.encode("utf-8"))
        for name, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "scheme": "http",
        "query_string": b"",
        "headers": raw_headers,
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 80),
        "http_version": "1.1",
    }
    return Request(scope)


def test_client_identifier_prefers_forwarded_for() -> None:
    request = _build_request({"x-forwarded-for": "203.0.113.1, 10.0.0.1"})

    assert _client_identifier(request) == "203.0.113.1"


def test_client_identifier_uses_explicit_client_id() -> None:
    request = _build_request({"x-client-id": "frontend-app"})

    assert _client_identifier(request) == "frontend-app"


def test_client_identifier_falls_back_to_remote_address(mocker) -> None:
    request = _build_request()
    remote_address = mocker.patch(
        "app.core.rate_limit.get_remote_address", return_value="198.51.100.8"
    )

    assert _client_identifier(request) == "198.51.100.8"
    remote_address.assert_called_once_with(request)


def test_is_rate_limiting_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "true")
    assert is_rate_limiting_enabled() is True

    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")
    assert is_rate_limiting_enabled() is False


def test_rate_limit_returns_relaxed_limit_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")
    resolver = rate_limit("RATE_LIMIT_TASKS", "10/minute")

    assert resolver() == "1000000/minute"


def test_rate_limit_uses_env_override_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_TASKS", " 55/minute ")
    resolver = rate_limit("RATE_LIMIT_TASKS", "10/minute")

    assert resolver() == "55/minute"
