import os

import pytest

from fastapi.testclient import TestClient
from app.core.database import init_database

if not os.getenv("DATABASE_URL", "").strip():
    pytest.skip("DATABASE_URL is required for integration tests", allow_module_level=True)

from main import app  # noqa: E402


def _reset_db() -> None:
    init_database()


def test_health_check() -> None:
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_tasks_crud_flow() -> None:
    _reset_db()
    client = TestClient(app)

    create_response = client.post(
        "/tasks",
        json={"title": "Write tests", "description": "Add API coverage"},
    )
    assert create_response.status_code == 201

    created = create_response.json()
    assert created["title"] == "Write tests"
    assert created["description"] == "Add API coverage"
    assert created["status"] == "todo"
    task_id = created["id"]

    list_response = client.get("/tasks")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["id"] == task_id

    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Write tests"

    get_by_name_response = client.get("/tasks/name/Write")
    assert get_by_name_response.status_code == 200
    assert get_by_name_response.json()["id"] == task_id

    patch_response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "done", "title": "Write and run tests"},
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["status"] == "done"
    assert patched["title"] == "Write and run tests"

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 204

    after_delete = client.get(f"/tasks/{task_id}")
    assert after_delete.status_code == 404


def test_not_found_paths() -> None:
    _reset_db()
    client = TestClient(app)

    get_missing = client.get("/tasks/999999")
    assert get_missing.status_code == 404

    get_by_name_missing = client.get("/tasks/name/not-existing-task")
    assert get_by_name_missing.status_code == 404

    get_by_name_invalid = client.get("/tasks/name/%20%20%20")
    assert get_by_name_invalid.status_code == 400

    patch_missing = client.patch("/tasks/999999", json={"status": "done"})
    assert patch_missing.status_code == 404

    delete_missing = client.delete("/tasks/999999")
    assert delete_missing.status_code == 404


def test_create_task_validation_error() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.post("/tasks", json={"description": "missing title"})
    assert response.status_code == 422


def test_create_task_sanitizes_html_input() -> None:
    _reset_db()
    client = TestClient(app)

    response = client.post(
        "/tasks",
        json={
            "title": "<script>alert(1)</script>Write <b>docs</b>",
            "description": "<img src=x onerror=alert(2)>Ship <i>release</i>",
        },
    )
    assert response.status_code == 201

    payload = response.json()
    assert payload["title"] == "alert(1)Write docs"
    assert payload["description"] == "Ship release"
