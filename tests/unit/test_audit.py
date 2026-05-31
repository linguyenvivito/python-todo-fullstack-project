import json

import pytest
from starlette.requests import Request

from app.core.audit import (
    AuditRepository,
    AuditService,
    _get_audit_service,
    audit_service,
)
from app.core.models import AuditLog


class _FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None) -> None:
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed: list[tuple[str, tuple]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple | list) -> None:
        self.executed.append((sql, tuple(params)))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def close(self) -> None:
        self.closed = True


class _FakeConnection:
    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.commit_count = 0
        self.cursor_kwargs: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self, **kwargs):
        self.cursor_kwargs.append(kwargs)
        return self._cursor

    def commit(self) -> None:
        self.commit_count += 1


def _request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "scheme": "http",
        "query_string": b"",
        "headers": [
            (b"x-request-id", b"req-1"),
            (b"user-agent", b"pytest-agent"),
        ],
        "client": ("127.0.0.1", 9999),
        "server": ("testserver", 80),
        "http_version": "1.1",
    }
    return Request(scope)


def _request_without_client() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "scheme": "http",
        "query_string": b"",
        "headers": [
            (b"x-request-id", b"req-2"),
            (b"user-agent", b"pytest-agent"),
        ],
        "client": None,
        "server": ("testserver", 80),
        "http_version": "1.1",
    }
    return Request(scope)


def _audit_row(**overrides):
    row = {
        "id": 1,
        "occurred_at": 1700000000,
        "actor_user_id": 10,
        "action": "auth.login",
        "resource_type": "user",
        "resource_id": "10",
        "success": True,
        "http_method": "POST",
        "path": "/auth/login",
        "status_code": 200,
        "client_ip": "127.0.0.1",
        "user_agent": "pytest-agent",
        "request_id": "req-1",
        "details_json": "{\"k\":\"v\"}",
    }
    row.update(overrides)
    return row


def test_audit_repository_init_calls_init_database(mocker) -> None:
    init_db = mocker.patch("app.core.audit.init_database")

    AuditRepository()

    init_db.assert_called_once_with()


def test_row_to_audit_log_maps_fields() -> None:
    log = AuditRepository._row_to_audit_log(_audit_row(success=1))

    assert isinstance(log, AuditLog)
    assert log.id == 1
    assert log.success is True
    assert log.action == "auth.login"


def test_create_inserts_and_returns_log(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=_audit_row())
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)

    repo = AuditRepository()
    log = repo.create(
        occurred_at=1700000000,
        actor_user_id=10,
        action="auth.login",
        resource_type="user",
        resource_id="10",
        success=True,
        http_method="POST",
        path="/auth/login",
        status_code=200,
        client_ip="127.0.0.1",
        user_agent="pytest-agent",
        request_id="req-1",
        details_json="{}",
    )

    assert log.id == 1
    assert connection.commit_count == 1
    assert cursor.closed is True


def test_create_raises_when_psycopg_not_available(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=_audit_row())
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)
    mocker.patch("app.core.audit.dict_row", None)

    repo = AuditRepository()

    with pytest.raises(RuntimeError, match="psycopg"):
        repo.create(
            occurred_at=1,
            actor_user_id=None,
            action="a",
            resource_type=None,
            resource_id=None,
            success=True,
            http_method=None,
            path=None,
            status_code=None,
            client_ip=None,
            user_agent=None,
            request_id=None,
            details_json=None,
        )


def test_create_raises_when_no_returned_row(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)

    repo = AuditRepository()

    with pytest.raises(RuntimeError, match="Failed to create audit log"):
        repo.create(
            occurred_at=1,
            actor_user_id=None,
            action="a",
            resource_type=None,
            resource_id=None,
            success=True,
            http_method=None,
            path=None,
            status_code=None,
            client_ip=None,
            user_agent=None,
            request_id=None,
            details_json=None,
        )


def test_build_filters_with_no_filters() -> None:
    where, params = AuditRepository._build_filters(
        action=None,
        success=None,
        actor_user_id=None,
        occurred_from=None,
        occurred_to=None,
        placeholder="%s",
    )

    assert where == ""
    assert params == []


def test_build_filters_with_all_filters() -> None:
    where, params = AuditRepository._build_filters(
        action="login",
        success=False,
        actor_user_id=5,
        occurred_from=100,
        occurred_to=200,
        placeholder="%s",
    )

    assert "LOWER(action) LIKE LOWER(%s)" in where
    assert "success = %s" in where
    assert "actor_user_id = %s" in where
    assert "occurred_at >= %s" in where
    assert "occurred_at <= %s" in where
    assert params == ["%login%", False, 5, 100, 200]


def test_list_returns_mapped_logs(mocker) -> None:
    cursor = _FakeCursor(fetchall_result=[_audit_row(id=2), _audit_row(id=1)])
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)

    repo = AuditRepository()
    items = repo.list(
        action="login",
        success=True,
        actor_user_id=10,
        occurred_from=1,
        occurred_to=2,
        limit=20,
        offset=5,
    )

    assert [item.id for item in items] == [2, 1]
    assert cursor.closed is True
    assert cursor.executed[0][1][-2:] == (20, 5)


def test_list_raises_when_psycopg_not_available(mocker) -> None:
    cursor = _FakeCursor(fetchall_result=[])
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)
    mocker.patch("app.core.audit.dict_row", None)

    repo = AuditRepository()

    with pytest.raises(RuntimeError, match="psycopg"):
        repo.list(
            action=None,
            success=None,
            actor_user_id=None,
            occurred_from=None,
            occurred_to=None,
            limit=10,
            offset=0,
        )


def test_count_returns_value(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=(7,))
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)

    repo = AuditRepository()
    total = repo.count(
        action="login",
        success=True,
        actor_user_id=10,
        occurred_from=1,
        occurred_to=2,
    )

    assert total == 7
    assert cursor.closed is True


def test_count_returns_zero_when_no_row(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.core.audit.init_database")
    mocker.patch("app.core.audit.get_connection", return_value=connection)

    repo = AuditRepository()

    assert (
        repo.count(
            action=None,
            success=None,
            actor_user_id=None,
            occurred_from=None,
            occurred_to=None,
        )
        == 0
    )


def test_clean_string_behaviors() -> None:
    assert AuditService._clean_string(None) is None
    assert AuditService._clean_string("   ") is None
    assert AuditService._clean_string(" abc ") == "abc"
    assert AuditService._clean_string("x" * 1000, max_length=10) == "x" * 10


def test_sanitize_details_redacts_and_serializes() -> None:
    value = AuditService._sanitize_details(
        {
            "Password": "secret-value",
            "token": "t",
            "count": 3,
            "ok": True,
            "meta": {"a": 1},
            "note": "x" * 600,
        }
    )

    assert value is not None
    parsed = json.loads(value)
    assert parsed["password"] == "[REDACTED]"
    assert parsed["token"] == "[REDACTED]"
    assert parsed["count"] == 3
    assert parsed["ok"] is True
    assert isinstance(parsed["meta"], str)
    assert len(parsed["note"]) == 512


def test_sanitize_details_returns_none_for_empty_inputs() -> None:
    assert AuditService._sanitize_details(None) is None
    assert AuditService._sanitize_details({}) is None


def test_sanitize_details_returns_none_for_truthy_mapping_without_items() -> None:
    class _TruthyEmptyMapping(dict):
        def __bool__(self) -> bool:
            return True

    assert AuditService._sanitize_details(_TruthyEmptyMapping()) is None


def test_record_event_with_request_uses_sanitized_data(mocker) -> None:
    repository = mocker.Mock()
    repository.create.return_value = AuditLog(
        id=1,
        occurred_at=1700000000,
        actor_user_id=10,
        action="auth.login",
        resource_type="user",
        resource_id="10",
        success=True,
        http_method="POST",
        path="/auth/login",
        status_code=200,
        client_ip="127.0.0.1",
        user_agent="pytest-agent",
        request_id="req-1",
        details_json="{}",
    )
    mocker.patch("app.core.audit.time.time", return_value=1700000000)
    service = AuditService(repository)

    result = service.record_event(
        action="  auth.login  ",
        success=True,
        request=_request(),
        actor_user_id=10,
        resource_type=" user ",
        resource_id=" 10 ",
        status_code=200,
        details={"password": "hidden", "note": "ok"},
    )

    assert result.id == 1
    kwargs = repository.create.call_args.kwargs
    assert kwargs["occurred_at"] == 1700000000
    assert kwargs["action"] == "auth.login"
    assert kwargs["http_method"] == "POST"
    assert kwargs["path"] == "/auth/login"
    assert kwargs["request_id"] == "req-1"
    assert kwargs["client_ip"] == "127.0.0.1"
    details = json.loads(kwargs["details_json"])
    assert details["password"] == "[REDACTED]"


def test_record_event_without_request_uses_defaults(mocker) -> None:
    repository = mocker.Mock()
    repository.create.return_value = AuditLog(
        id=1,
        occurred_at=1,
        actor_user_id=None,
        action="unknown.action",
        resource_type=None,
        resource_id=None,
        success=False,
        http_method=None,
        path=None,
        status_code=None,
        client_ip=None,
        user_agent=None,
        request_id=None,
        details_json=None,
    )
    mocker.patch("app.core.audit.time.time", return_value=1)
    service = AuditService(repository)

    service.record_event(action="   ", success=False, request=None, details=None)

    kwargs = repository.create.call_args.kwargs
    assert kwargs["action"] == "unknown.action"
    assert kwargs["http_method"] is None
    assert kwargs["path"] is None
    assert kwargs["details_json"] is None


def test_record_event_with_request_without_client_sets_client_ip_none(mocker) -> None:
    repository = mocker.Mock()
    repository.create.return_value = AuditLog(
        id=2,
        occurred_at=2,
        actor_user_id=None,
        action="auth.login",
        resource_type=None,
        resource_id=None,
        success=True,
        http_method="POST",
        path="/auth/login",
        status_code=200,
        client_ip=None,
        user_agent="pytest-agent",
        request_id="req-2",
        details_json=None,
    )
    mocker.patch("app.core.audit.time.time", return_value=2)
    service = AuditService(repository)

    service.record_event(action="auth.login", success=True, request=_request_without_client())

    kwargs = repository.create.call_args.kwargs
    assert kwargs["client_ip"] is None


def test_list_events_cleans_action_and_returns_items_total(mocker) -> None:
    repository = mocker.Mock()
    expected_items = [
        AuditLog(
            id=1,
            occurred_at=1,
            actor_user_id=1,
            action="auth.login",
            resource_type=None,
            resource_id=None,
            success=True,
            http_method="POST",
            path="/auth/login",
            status_code=200,
            client_ip=None,
            user_agent=None,
            request_id=None,
            details_json=None,
        )
    ]
    repository.list.return_value = expected_items
    repository.count.return_value = 9
    service = AuditService(repository)

    items, total = service.list_events(
        action="  LOGIN  ",
        success=True,
        actor_user_id=1,
        occurred_from=10,
        occurred_to=20,
        limit=50,
        offset=0,
    )

    assert items == expected_items
    assert total == 9
    assert repository.list.call_args.kwargs["action"] == "LOGIN"
    assert repository.count.call_args.kwargs["action"] == "LOGIN"


def test_get_audit_service_is_cached(mocker) -> None:
    _get_audit_service.cache_clear()
    repository = object()
    service = object()
    repo_cls = mocker.patch("app.core.audit.AuditRepository", return_value=repository)
    service_cls = mocker.patch("app.core.audit.AuditService", return_value=service)

    first = _get_audit_service()
    second = _get_audit_service()

    assert first is second
    repo_cls.assert_called_once_with()
    service_cls.assert_called_once_with(repository)


def test_lazy_audit_service_delegates_calls(mocker) -> None:
    fake_service = mocker.Mock()
    fake_service.record_event.return_value = "recorded"
    fake_service.list_events.return_value = ([], 0)
    mocker.patch("app.core.audit._get_audit_service", return_value=fake_service)

    assert audit_service.record_event(action="a", success=True) == "recorded"
    assert audit_service.list_events(action=None, success=None, actor_user_id=None, occurred_from=None, occurred_to=None, limit=1, offset=0) == ([], 0)

    fake_service.record_event.assert_called_once()
    fake_service.list_events.assert_called_once()
