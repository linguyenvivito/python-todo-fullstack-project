from contextlib import contextmanager

import pytest

import app.slices.tasks.repository as repository_module
from app.core.models import Task, TaskStatus
from app.slices.tasks.repository import TaskRepository


class _FakeCursor:
    def __init__(self, *, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.executed = []
        self.closed = False

    def execute(self, query, params=None) -> None:
        self.executed.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def close(self) -> None:
        self.closed = True


class _FakeConnection:
    def __init__(self, cursors):
        self._cursors = list(cursors)
        self.commit_calls = 0
        self.row_factories = []

    def cursor(self, row_factory=None):
        self.row_factories.append(row_factory)
        return self._cursors.pop(0)

    def commit(self) -> None:
        self.commit_calls += 1


def _make_repository(mocker, connection: _FakeConnection) -> TaskRepository:
    mocker.patch.object(repository_module, "init_database", lambda: None)
    mocker.patch.object(repository_module, "dict_row", object())

    @contextmanager
    def _fake_get_connection():
        yield connection

    mocker.patch.object(repository_module, "get_connection", _fake_get_connection)
    return TaskRepository()


def test_create_uses_cursor_and_returns_id(mocker) -> None:
    cursor = _FakeCursor(fetchone_result={"id": 101})
    connection = _FakeConnection([cursor])
    repository = _make_repository(mocker, connection)

    created = repository.create(title="PG Task", description="PG Desc")

    assert created.id == 101
    assert created.status == TaskStatus.TODO
    assert connection.commit_calls == 1
    assert cursor.closed is True
    assert len(cursor.executed) == 1


def test_create_raises_when_insert_returns_no_id(mocker) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection([cursor])
    repository = _make_repository(mocker, connection)

    with pytest.raises(RuntimeError, match="INSERT did not return a task id"):
        repository.create(title="PG Task")

    assert cursor.closed is True


def test_list_all_maps_rows(mocker) -> None:
    cursor = _FakeCursor(
        fetchall_result=[
            {"id": 1, "title": "A", "description": None, "status": "todo"},
            {"id": 2, "title": "B", "description": "d", "status": "done"},
        ]
    )
    connection = _FakeConnection([cursor])
    repository = _make_repository(mocker, connection)

    tasks = repository.list_all()

    assert [task.id for task in tasks] == [1, 2]
    assert tasks[1].status == TaskStatus.DONE
    assert cursor.closed is True


def test_get_by_id_paths(mocker) -> None:
    existing_cursor = _FakeCursor(
        fetchone_result={"id": 9, "title": "Found", "description": None, "status": "todo"}
    )
    missing_cursor = _FakeCursor(fetchone_result=None)
    existing_connection = _FakeConnection([existing_cursor])
    missing_connection = _FakeConnection([missing_cursor])

    repository = _make_repository(mocker, existing_connection)
    found = repository.get_by_id(9)

    repository = _make_repository(mocker, missing_connection)
    missing = repository.get_by_id(999)

    assert found is not None
    assert found.id == 9
    assert missing is None
    assert existing_cursor.closed is True
    assert missing_cursor.closed is True


def test_update_and_delete_queries(mocker) -> None:
    update_cursor = _FakeCursor()
    delete_cursor = _FakeCursor()
    update_connection = _FakeConnection([update_cursor])
    delete_connection = _FakeConnection([delete_cursor])

    repository = _make_repository(mocker, update_connection)
    task = Task(id=3, title="U", description="D", status=TaskStatus.IN_PROGRESS)
    repository.update(task)

    repository = _make_repository(mocker, delete_connection)
    repository.delete(3)

    assert "UPDATE tasks" in update_cursor.executed[0][0]
    assert update_connection.commit_calls == 1
    assert update_cursor.closed is True
    assert "DELETE FROM tasks" in delete_cursor.executed[0][0]
    assert delete_connection.commit_calls == 1
    assert delete_cursor.closed is True


@pytest.mark.parametrize("method_name", ["create", "list_all", "get_by_id"])
def test_requires_psycopg_row_factory(mocker, method_name: str) -> None:
    connection = _FakeConnection([_FakeCursor(fetchone_result={"id": 1})])
    mocker.patch.object(repository_module, "init_database", lambda: None)
    mocker.patch.object(repository_module, "dict_row", None)

    @contextmanager
    def _fake_get_connection():
        yield connection

    mocker.patch.object(repository_module, "get_connection", _fake_get_connection)
    repository = TaskRepository()

    if method_name == "create":

        def call() -> object:
            return repository.create("x")
    elif method_name == "list_all":
        call = repository.list_all
    else:

        def call() -> object:
            return repository.get_by_id(1)

    with pytest.raises(RuntimeError, match="PostgreSQL mode requires psycopg"):
        call()
