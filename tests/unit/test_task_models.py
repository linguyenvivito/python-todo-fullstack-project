import pytest
from pydantic import ValidationError

from app.core.models import TaskStatus
from app.slices.tasks.models import TaskCreateRequest, TaskResponse, TaskUpdateRequest


def test_task_create_request_accepts_valid_payload() -> None:
    payload = TaskCreateRequest(title="Task", description="Description")

    assert payload.title == "Task"
    assert payload.description == "Description"


def test_task_create_request_requires_title() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest.model_validate({"description": "Missing title"})


def test_task_create_request_validates_title_length() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="")


def test_task_create_request_validates_description_max_length() -> None:
    with pytest.raises(ValidationError):
        TaskCreateRequest(title="Task", description="a" * 501)


def test_task_update_request_validates_status_enum() -> None:
    with pytest.raises(ValidationError):
        TaskUpdateRequest.model_validate({"status": "invalid"})


def test_task_update_request_allows_partial_fields() -> None:
    payload = TaskUpdateRequest(status=TaskStatus.DONE)

    assert payload.status == TaskStatus.DONE
    assert payload.title is None
    assert payload.description is None


def test_task_update_request_allows_archived_status() -> None:
    payload = TaskUpdateRequest(status=TaskStatus.ARCHIVED)

    assert payload.status == TaskStatus.ARCHIVED


def test_task_response_validates_output_shape() -> None:
    response = TaskResponse(id=1, title="Task", description=None, status=TaskStatus.TODO)

    assert response.id == 1
    assert response.status == TaskStatus.TODO
