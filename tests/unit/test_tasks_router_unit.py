from typing import Optional, Union

from fastapi.testclient import TestClient

from app.core.exceptions import InvalidTaskSearchError, TaskNotFoundByNameError, TaskNotFoundError
from app.core.models import Task, TaskStatus
from app.slices.tasks.models import TaskCreateRequest, TaskUpdateRequest
from app.slices.tasks import router as tasks_router_module
from main import app


class FakeTaskService:
    def __init__(self) -> None:
        self.create_result = Task(id=1, title="Created", description="Desc", status=TaskStatus.TODO)
        self.list_result = [self.create_result]
        self.get_result: Optional[Task] = self.create_result
        self.get_by_name_result: Optional[Task] = self.create_result
        self.update_result: Optional[Task] = Task(
            id=1,
            title="Updated",
            description="Desc",
            status=TaskStatus.DONE,
        )
        self.create_payload: Optional[TaskCreateRequest] = None
        self.update_payload: Optional[TaskUpdateRequest] = None
        self.deleted_task_id: Optional[Union[int, str]] = None

    def create_task(self, payload: TaskCreateRequest) -> Task:
        self.create_payload = payload
        return self.create_result

    def list_tasks(self):
        return self.list_result

    def get_task(self, task_id: int) -> Task:
        if self.get_result is None:
            raise TaskNotFoundError(task_id)
        return self.get_result

    def get_task_by_name(self, task_name: str) -> Task:
        if task_name.strip() == "invalid":
            raise InvalidTaskSearchError()
        if self.get_by_name_result is None:
            raise TaskNotFoundByNameError(task_name)
        return self.get_by_name_result

    def update_task(self, task_id: int, payload: TaskUpdateRequest) -> Task:
        if self.update_result is None:
            raise TaskNotFoundError(task_id)
        self.update_payload = payload
        return self.update_result

    def delete_task(self, task_id: int) -> None:
        if self.deleted_task_id == "RAISE":
            raise TaskNotFoundError(task_id)
        self.deleted_task_id = task_id


def _client_with_service(fake_service: FakeTaskService) -> TestClient:
    app.dependency_overrides[tasks_router_module.get_task_service] = lambda: fake_service
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_router_create_task_uses_service_payload() -> None:
    fake_service = FakeTaskService()
    client = _client_with_service(fake_service)

    response = client.post("/tasks", json={"title": "Created", "description": "Desc"})

    _clear_overrides()
    assert response.status_code == 201
    assert response.json()["title"] == "Created"
    assert fake_service.create_payload is not None
    assert fake_service.create_payload.title == "Created"


def test_router_maps_not_found_to_404_for_get_by_id() -> None:
    fake_service = FakeTaskService()
    fake_service.get_result = None
    client = _client_with_service(fake_service)

    response = client.get("/tasks/123")

    _clear_overrides()
    assert response.status_code == 404


def test_router_get_by_name_returns_task() -> None:
    fake_service = FakeTaskService()
    client = _client_with_service(fake_service)

    response = client.get("/tasks/name/Cre")

    _clear_overrides()
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_router_get_by_name_maps_not_found_to_404() -> None:
    fake_service = FakeTaskService()
    fake_service.get_by_name_result = None
    client = _client_with_service(fake_service)

    response = client.get("/tasks/name/Unknown")

    _clear_overrides()
    assert response.status_code == 404


def test_router_get_by_name_maps_invalid_search_to_400() -> None:
    fake_service = FakeTaskService()
    client = _client_with_service(fake_service)

    response = client.get("/tasks/name/invalid")

    _clear_overrides()
    assert response.status_code == 400


def test_router_update_404_when_service_raises_not_found() -> None:
    fake_service = FakeTaskService()
    fake_service.update_result = None
    client = _client_with_service(fake_service)

    response = client.patch("/tasks/99", json={"status": "done"})

    _clear_overrides()
    assert response.status_code == 404


def test_router_delete_returns_204() -> None:
    fake_service = FakeTaskService()
    client = _client_with_service(fake_service)

    response = client.delete("/tasks/1")

    _clear_overrides()
    assert response.status_code == 204
    assert fake_service.deleted_task_id == 1


def test_router_delete_404_when_service_raises() -> None:
    fake_service = FakeTaskService()
    fake_service.deleted_task_id = "RAISE"
    client = _client_with_service(fake_service)

    response = client.delete("/tasks/1")

    _clear_overrides()
    assert response.status_code == 404
