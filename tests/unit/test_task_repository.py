from pathlib import Path
from contextlib import contextmanager

import pytest

import app.slices.tasks.repository as repository_module
from app.core.models import Task, TaskStatus
from app.slices.tasks.repository import TaskRepository


def _make_repository(tmp_path: Path, monkeypatch) -> TaskRepository:
    db_path = tmp_path / "repo_test.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))
    return TaskRepository()


def test_create_persists_task_with_default_status(tmp_path: Path, monkeypatch) -> None:
    repository = _make_repository(tmp_path, monkeypatch)

    task = repository.create(title="Task 1", description="Desc")

    assert task.id > 0
    assert task.status == TaskStatus.TODO


def test_list_all_returns_tasks_in_id_order(tmp_path: Path, monkeypatch) -> None:
    repository = _make_repository(tmp_path, monkeypatch)
    first = repository.create(title="First")
    second = repository.create(title="Second")

    tasks = repository.list_all()

    assert [task.id for task in tasks] == [first.id, second.id]
    assert tasks[1].title == "Second"


def test_get_by_id_returns_none_when_missing(tmp_path: Path, monkeypatch) -> None:
    repository = _make_repository(tmp_path, monkeypatch)

    task = repository.get_by_id(999)

    assert task is None


def test_update_persists_task_changes(tmp_path: Path, monkeypatch) -> None:
    repository = _make_repository(tmp_path, monkeypatch)
    created = repository.create(title="Original", description="Original",)
    updated_task = Task(
        id=created.id,
        title="Updated",
        description="Updated desc",
        status=TaskStatus.DONE,
    )

    repository.update(updated_task)
    fetched = repository.get_by_id(created.id)

    assert fetched is not None
    assert fetched.title == "Updated"
    assert fetched.description == "Updated desc"
    assert fetched.status == TaskStatus.DONE


def test_delete_removes_task(tmp_path: Path, monkeypatch) -> None:
    repository = _make_repository(tmp_path, monkeypatch)
    created = repository.create(title="To delete")

    repository.delete(created.id)

    assert repository.get_by_id(created.id) is None


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


def _make_postgres_repository(monkeypatch, connection: _FakeConnection) -> TaskRepository:
    monkeypatch.setattr(repository_module, "init_database", lambda: None)
    monkeypatch.setattr(repository_module, "use_postgres", lambda: True)
    monkeypatch.setattr(repository_module, "dict_row", object())

    @contextmanager
    def _fake_get_connection():
        yield connection

    monkeypatch.setattr(repository_module, "get_connection", _fake_get_connection)
    return TaskRepository()


def test_create_uses_postgres_cursor_and_returns_id(monkeypatch) -> None:
    cursor = _FakeCursor(fetchone_result={"id": 101})
    connection = _FakeConnection([cursor])
    repository = _make_postgres_repository(monkeypatch, connection)

    created = repository.create(title="PG Task", description="PG Desc")

    assert created.id == 101
    assert created.status == TaskStatus.TODO
    assert connection.commit_calls == 1
    assert cursor.closed is True
    assert len(cursor.executed) == 1


def test_create_postgres_raises_when_insert_returns_no_id(monkeypatch) -> None:
    cursor = _FakeCursor(fetchone_result=None)
    connection = _FakeConnection([cursor])
    repository = _make_postgres_repository(monkeypatch, connection)

    with pytest.raises(RuntimeError, match="INSERT did not return a task id"):
        repository.create(title="PG Task")

    assert cursor.closed is True


def test_list_all_uses_postgres_and_maps_rows(monkeypatch) -> None:
    cursor = _FakeCursor(
        fetchall_result=[
            {"id": 1, "title": "A", "description": None, "status": "todo"},
            {"id": 2, "title": "B", "description": "d", "status": "done"},
        ]
    )
    connection = _FakeConnection([cursor])
    repository = _make_postgres_repository(monkeypatch, connection)

    tasks = repository.list_all()

    assert [task.id for task in tasks] == [1, 2]
    assert tasks[1].status == TaskStatus.DONE
    assert cursor.closed is True


def test_get_by_id_uses_postgres_paths(monkeypatch) -> None:
    existing_cursor = _FakeCursor(
        fetchone_result={"id": 9, "title": "Found", "description": None, "status": "todo"}
    )
    missing_cursor = _FakeCursor(fetchone_result=None)
    existing_connection = _FakeConnection([existing_cursor])
    missing_connection = _FakeConnection([missing_cursor])

    repository = _make_postgres_repository(monkeypatch, existing_connection)
    found = repository.get_by_id(9)

    repository = _make_postgres_repository(monkeypatch, missing_connection)
    missing = repository.get_by_id(999)

    assert found is not None
    assert found.id == 9
    assert missing is None
    assert existing_cursor.closed is True
    assert missing_cursor.closed is True


def test_update_and_delete_use_postgres_queries(monkeypatch) -> None:
    update_cursor = _FakeCursor()
    delete_cursor = _FakeCursor()
    update_connection = _FakeConnection([update_cursor])
    delete_connection = _FakeConnection([delete_cursor])

    repository = _make_postgres_repository(monkeypatch, update_connection)
    task = Task(id=3, title="U", description="D", status=TaskStatus.IN_PROGRESS)
    repository.update(task)

    repository = _make_postgres_repository(monkeypatch, delete_connection)
    repository.delete(3)

    assert "UPDATE tasks" in update_cursor.executed[0][0]
    assert update_connection.commit_calls == 1
    assert update_cursor.closed is True
    assert "DELETE FROM tasks" in delete_cursor.executed[0][0]
    assert delete_connection.commit_calls == 1
    assert delete_cursor.closed is True


@pytest.mark.parametrize("method_name", ["create", "list_all", "get_by_id"])
def test_postgres_mode_requires_psycopg_row_factory(monkeypatch, method_name: str) -> None:
    connection = _FakeConnection([_FakeCursor(fetchone_result={"id": 1})])
    monkeypatch.setattr(repository_module, "init_database", lambda: None)
    monkeypatch.setattr(repository_module, "use_postgres", lambda: True)
    monkeypatch.setattr(repository_module, "dict_row", None)

    @contextmanager
    def _fake_get_connection():
        yield connection

    monkeypatch.setattr(repository_module, "get_connection", _fake_get_connection)
    repository = TaskRepository()

    if method_name == "create":
        call = lambda: repository.create("x")
    elif method_name == "list_all":
        call = repository.list_all
    else:
        call = lambda: repository.get_by_id(1)

    with pytest.raises(RuntimeError, match="PostgreSQL mode requires psycopg"):
        call()
