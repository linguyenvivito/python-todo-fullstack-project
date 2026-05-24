from pathlib import Path

from app.core.models import Task, TaskStatus
from app.slices.tasks.repository import TaskRepository


def _make_repository(tmp_path: Path, monkeypatch) -> TaskRepository:
    db_path = tmp_path / "repo_test.db"
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
