import importlib
from contextlib import contextmanager
from typing import Optional, Union

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import InvalidTaskSearchError, TaskNotFoundByNameError, TaskNotFoundError
from app.core.models import Task, TaskStatus, User
from app.slices.tasks.models import TaskCreateRequest, TaskUpdateRequest


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


@pytest.fixture
def client_and_service(mocker):
    fake_service = FakeTaskService()

    class _NoopCursor:
        description = [("id",), ("occurred_at",), ("actor_user_id",), ("action",)]

        def execute(self, _query, _params=None):
            return None

        def fetchone(self):
            return None

        def fetchall(self):
            return []

        def close(self) -> None:
            return None

    class _NoopConnection:
        def cursor(self, row_factory=None):
            del row_factory
            return _NoopCursor()

        def commit(self) -> None:
            return None

        def close(self) -> None:
            return None

    @contextmanager
    def _fake_get_connection():
        yield _NoopConnection()

    # Prevent router/auth/audit import-time DB calls from requiring real PostgreSQL.
    mocker.patch("app.core.database.get_connection", _fake_get_connection)

    import app.slices.tasks.router as tasks_router_module
    import main as main_module
    from app.slices.auth.dependencies import get_request_user

    importlib.reload(tasks_router_module)
    importlib.reload(main_module)

    app = main_module.create_app()
    app.dependency_overrides[tasks_router_module.get_task_service] = lambda: fake_service
    app.dependency_overrides[get_request_user] = lambda: User(id=0, username="", password_hash="")

    mocker.patch.object(tasks_router_module.audit_service, "record_event", return_value=None)

    client = TestClient(app)
    return client, fake_service


def test_router_create_task_uses_service_payload(client_and_service) -> None:
    client, fake_service = client_and_service

    response = client.post("/tasks", json={"title": "Created", "description": "Desc"})

    assert response.status_code == 201
    assert response.json()["title"] == "Created"
    assert fake_service.create_payload is not None
    assert fake_service.create_payload.title == "Created"


def test_router_maps_not_found_to_404_for_get_by_id(client_and_service) -> None:
    client, fake_service = client_and_service
    fake_service.get_result = None

    response = client.get("/tasks/123")

    assert response.status_code == 404


def test_router_get_by_name_returns_task(client_and_service) -> None:
    client, _ = client_and_service

    response = client.get("/tasks/name/Cre")

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_router_get_by_name_maps_not_found_to_404(client_and_service) -> None:
    client, fake_service = client_and_service
    fake_service.get_by_name_result = None

    response = client.get("/tasks/name/Unknown")

    assert response.status_code == 404


def test_router_get_by_name_maps_invalid_search_to_400(client_and_service) -> None:
    client, _ = client_and_service

    response = client.get("/tasks/name/invalid")

    assert response.status_code == 400


def test_router_update_404_when_service_raises_not_found(client_and_service) -> None:
    client, fake_service = client_and_service
    fake_service.update_result = None

    response = client.patch("/tasks/99", json={"status": "done"})

    assert response.status_code == 404


def test_router_delete_returns_204(client_and_service) -> None:
    client, fake_service = client_and_service

    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert fake_service.deleted_task_id == 1


def test_router_delete_404_when_service_raises(client_and_service) -> None:
    client, fake_service = client_and_service
    fake_service.deleted_task_id = "RAISE"

    response = client.delete("/tasks/1")

    assert response.status_code == 404
