import pytest

from app.core.models import User
from app.slices.auth.repository import (
    RefreshTokenRecord,
    RefreshTokenRepository,
    UserRepository,
)


class _FakeCursor:
    def __init__(self, fetchone_result=None) -> None:
        self.fetchone_result = fetchone_result
        self.executed: list[tuple[str, tuple]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple) -> None:
        self.executed.append((sql, params))

    def fetchone(self):
        return self.fetchone_result

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


def test_user_repository_init_calls_init_database(mocker) -> None:
    init_db = mocker.patch("app.slices.auth.repository.init_database")

    UserRepository()

    init_db.assert_called_once_with()


def test_refresh_token_repository_init_calls_init_database(mocker) -> None:
    init_db = mocker.patch("app.slices.auth.repository.init_database")

    RefreshTokenRepository()

    init_db.assert_called_once_with()


def test_row_to_user_maps_fields() -> None:
    row = {"id": 1, "username": "alice", "password_hash": "hash"}

    user = UserRepository._row_to_user(row)

    assert user == User(id=1, username="alice", password_hash="hash")


def test_create_inserts_and_returns_user(mocker) -> None:
    cursor = _FakeCursor(fetchone_result={"id": 2, "username": "bob", "password_hash": "h"})
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = UserRepository()
    user = repo.create("bob", "h")

    assert user == User(id=2, username="bob", password_hash="h")
    assert connection.commit_count == 1
    assert cursor.closed is True
    assert cursor.executed[0][1] == ("bob", "h")


def test_create_raises_when_psycopg_not_available(mocker) -> None:
    cursor = _FakeCursor(fetchone_result={"id": 2, "username": "bob", "password_hash": "h"})
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)
    mocker.patch("app.slices.auth.repository.dict_row", None)

    repo = UserRepository()

    with pytest.raises(RuntimeError, match="psycopg"):
        repo.create("bob", "h")


def test_create_raises_when_insert_returns_no_row(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = UserRepository()

    with pytest.raises(RuntimeError, match="Failed to create user"):
        repo.create("bob", "h")


def test_get_by_username_returns_user(mocker) -> None:
    cursor = _FakeCursor(fetchone_result={"id": 5, "username": "eve", "password_hash": "pw"})
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = UserRepository()
    result = repo.get_by_username("eve")

    assert result == User(id=5, username="eve", password_hash="pw")
    assert cursor.closed is True
    assert cursor.executed[0][1] == ("eve",)


def test_get_by_username_returns_none_when_not_found(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = UserRepository()

    assert repo.get_by_username("missing") is None


def test_get_by_username_raises_when_psycopg_not_available(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)
    mocker.patch("app.slices.auth.repository.dict_row", None)

    repo = UserRepository()

    with pytest.raises(RuntimeError, match="psycopg"):
        repo.get_by_username("alice")


def test_get_by_id_returns_user(mocker) -> None:
    cursor = _FakeCursor(fetchone_result={"id": 8, "username": "mia", "password_hash": "pw"})
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = UserRepository()
    result = repo.get_by_id(8)

    assert result == User(id=8, username="mia", password_hash="pw")
    assert cursor.executed[0][1] == (8,)


def test_get_by_id_returns_none_when_not_found(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = UserRepository()

    assert repo.get_by_id(999) is None


def test_get_by_id_raises_when_psycopg_not_available(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)
    mocker.patch("app.slices.auth.repository.dict_row", None)

    repo = UserRepository()

    with pytest.raises(RuntimeError, match="psycopg"):
        repo.get_by_id(1)


def test_row_to_refresh_record_maps_fields() -> None:
    row = {
        "jti": "j1",
        "user_id": 10,
        "expires_at": 1234,
        "revoked_at": None,
        "replaced_by_jti": "j2",
    }

    record = RefreshTokenRepository._row_to_record(row)

    assert record == RefreshTokenRecord(
        jti="j1",
        user_id=10,
        expires_at=1234,
        revoked_at=None,
        replaced_by_jti="j2",
    )


def test_refresh_store_executes_insert_and_commits(mocker) -> None:
    cursor = _FakeCursor()
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = RefreshTokenRepository()
    repo.store("j1", 7, 9999)

    assert connection.commit_count == 1
    assert cursor.closed is True
    assert cursor.executed[0][1] == ("j1", 7, 9999)


def test_refresh_get_returns_record(mocker) -> None:
    cursor = _FakeCursor(
        fetchone_result={
            "jti": "j1",
            "user_id": 7,
            "expires_at": 9999,
            "revoked_at": None,
            "replaced_by_jti": None,
        }
    )
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = RefreshTokenRepository()
    record = repo.get("j1")

    assert record == RefreshTokenRecord(
        jti="j1",
        user_id=7,
        expires_at=9999,
        revoked_at=None,
        replaced_by_jti=None,
    )


def test_refresh_get_returns_none_when_not_found(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = RefreshTokenRepository()

    assert repo.get("missing") is None


def test_refresh_get_raises_when_psycopg_not_available(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)
    mocker.patch("app.slices.auth.repository.dict_row", None)

    repo = RefreshTokenRepository()

    with pytest.raises(RuntimeError, match="psycopg"):
        repo.get("j1")


def test_refresh_revoke_updates_and_commits(mocker) -> None:
    cursor = _FakeCursor()
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = RefreshTokenRepository()
    repo.revoke("j1", revoked_at=100, replaced_by_jti="j2")

    assert connection.commit_count == 1
    assert cursor.closed is True
    assert cursor.executed[0][1] == (100, "j2", "j1")


def test_refresh_revoke_all_for_user_updates_and_commits(mocker) -> None:
    cursor = _FakeCursor()
    connection = _FakeConnection(cursor)
    mocker.patch("app.slices.auth.repository.init_database")
    mocker.patch("app.slices.auth.repository.get_connection", return_value=connection)

    repo = RefreshTokenRepository()
    repo.revoke_all_for_user(user_id=22, revoked_at=111)

    assert connection.commit_count == 1
    assert cursor.closed is True
    assert cursor.executed[0][1] == (111, 22)
