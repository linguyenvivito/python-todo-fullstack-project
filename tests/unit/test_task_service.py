from unittest.mock import Mock

import pytest

from app.core.exceptions import InvalidTaskSearchError, TaskNotFoundByNameError, TaskNotFoundError
from app.core.models import Task, TaskStatus
from app.slices.tasks.models import TaskCreateRequest, TaskUpdateRequest
from app.slices.tasks.service import TaskService


def _task(task_id=1, title="Task 1", description="desc", status=TaskStatus.TODO):
    return Task(id=task_id, title=title, description=description, status=status)


def test_create_task_calls_repository_create() -> None:
    repository = Mock()
    repository.create.return_value = _task()
    service = TaskService(repository)

    payload = TaskCreateRequest(title="Task 1", description="desc")
    task = service.create_task(payload)

    repository.create.assert_called_once_with(title="Task 1", description="desc")
    assert task.id == 1


def test_list_tasks_returns_repository_data() -> None:
    repository = Mock()
    repository.list_all.return_value = [_task(task_id=1), _task(task_id=2, title="Task 2")]
    service = TaskService(repository)

    tasks = service.list_tasks()

    repository.list_all.assert_called_once()
    assert len(tasks) == 2
    assert tasks[1].title == "Task 2"


def test_get_task_returns_task_when_found() -> None:
    repository = Mock()
    repository.get_by_id.return_value = _task(task_id=5)
    service = TaskService(repository)

    task = service.get_task(5)

    repository.get_by_id.assert_called_once_with(5)
    assert task.id == 5


def test_get_task_raises_when_missing() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None
    service = TaskService(repository)

    with pytest.raises(TaskNotFoundError) as exc:
        service.get_task(42)

    repository.get_by_id.assert_called_once_with(42)
    assert exc.value.task_id == 42


def test_get_task_by_name_returns_matching_task() -> None:
    repository = Mock()
    repository.list_all.return_value = [
        _task(task_id=1, title="Write docs"),
        _task(task_id=2, title="Run tests"),
    ]
    service = TaskService(repository)

    task = service.get_task_by_name("Run")

    repository.list_all.assert_called_once()
    assert task.id == 2


def test_get_task_by_name_raises_when_missing() -> None:
    repository = Mock()
    repository.list_all.return_value = [_task(task_id=1, title="Write docs")]
    service = TaskService(repository)

    with pytest.raises(TaskNotFoundByNameError) as exc:
        service.get_task_by_name("Not found")

    assert exc.value.task_name == "Not found"


def test_get_task_by_name_raises_for_empty_search_term() -> None:
    repository = Mock()
    service = TaskService(repository)

    with pytest.raises(InvalidTaskSearchError):
        service.get_task_by_name("   ")

    repository.list_all.assert_not_called()


def test_update_task_applies_only_provided_fields() -> None:
    repository = Mock()
    existing = _task(task_id=3, title="Old", description="Old desc", status=TaskStatus.TODO)
    repository.get_by_id.return_value = existing
    repository.update.return_value = existing
    service = TaskService(repository)

    payload = TaskUpdateRequest(title="New", description="New desc", status=TaskStatus.DONE)
    updated = service.update_task(3, payload)

    assert updated.title == "New"
    assert updated.description == "New desc"
    assert updated.status == TaskStatus.DONE
    repository.update.assert_called_once()


def test_update_task_keeps_existing_fields_when_none() -> None:
    repository = Mock()
    existing = _task(task_id=7, title="Keep", description="Keep desc", status=TaskStatus.IN_PROGRESS)
    repository.get_by_id.return_value = existing
    repository.update.return_value = existing
    service = TaskService(repository)

    payload = TaskUpdateRequest()
    updated = service.update_task(7, payload)

    assert updated.title == "Keep"
    assert updated.description == "Keep desc"
    assert updated.status == TaskStatus.IN_PROGRESS


def test_delete_task_calls_repository_delete() -> None:
    repository = Mock()
    repository.get_by_id.return_value = _task(task_id=9)
    service = TaskService(repository)

    service.delete_task(9)

    repository.get_by_id.assert_called_once_with(9)
    repository.delete.assert_called_once_with(9)


def test_delete_task_raises_when_missing() -> None:
    repository = Mock()
    repository.get_by_id.return_value = None
    service = TaskService(repository)

    with pytest.raises(TaskNotFoundError):
        service.delete_task(111)

    repository.delete.assert_not_called()
