from contextlib import contextmanager
import os

import pytest

import app.core.database as database_module


def test_get_database_url_reads_env(mocker) -> None:
    mocker.patch.dict(os.environ, {"DATABASE_URL": "  postgresql://example  "})

    assert database_module.get_database_url() == "postgresql://example"


def test_get_connection_requires_database_url(mocker) -> None:
    mocker.patch.dict(os.environ, {"DATABASE_URL": ""})

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        with database_module.get_connection():
            pass


def test_get_connection_requires_psycopg_when_url_set(mocker) -> None:
    mocker.patch.dict(os.environ, {"DATABASE_URL": "postgresql://example"})
    mocker.patch.object(database_module, "psycopg", None)

    with pytest.raises(RuntimeError, match="psycopg is not installed"):
        with database_module.get_connection():
            pass


def test_get_connection_postgres_uses_connect_and_closes(mocker) -> None:
    class FakeConnection:
        def __init__(self):
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class FakePsycopg:
        def __init__(self):
            self.calls = []
            self.connection = FakeConnection()

        def connect(self, url):
            self.calls.append(url)
            return self.connection

    fake_psycopg = FakePsycopg()
    mocker.patch.dict(os.environ, {"DATABASE_URL": "postgresql://example"})
    mocker.patch.object(database_module, "psycopg", fake_psycopg)

    with database_module.get_connection() as connection:
        assert connection is fake_psycopg.connection

    assert fake_psycopg.calls == ["postgresql://example"]
    assert fake_psycopg.connection.closed is True


def test_init_database_postgres_uses_cursor_and_closes(mocker) -> None:
    class FakeCursor:
        def __init__(self):
            self.executed_sql = []
            self.closed = False

        def execute(self, sql):
            self.executed_sql.append(sql)

        def close(self) -> None:
            self.closed = True

    class FakeConnection:
        def __init__(self):
            self.cursor_obj = FakeCursor()
            self.commit_calls = 0

        def cursor(self):
            return self.cursor_obj

        def commit(self) -> None:
            self.commit_calls += 1

    fake_connection = FakeConnection()

    @contextmanager
    def fake_get_connection():
        yield fake_connection

    mocker.patch.object(database_module, "get_connection", fake_get_connection)

    database_module.init_database()

    assert len(fake_connection.cursor_obj.executed_sql) == 1
    assert "BIGSERIAL" in fake_connection.cursor_obj.executed_sql[0]
    assert "refresh_tokens" in fake_connection.cursor_obj.executed_sql[0]
    assert fake_connection.cursor_obj.closed is True
    assert fake_connection.commit_calls == 1
