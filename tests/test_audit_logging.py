import json
import os

from fastapi.testclient import TestClient
import pytest

from app.core.database import get_connection, init_database

if not os.getenv("DATABASE_URL", "").strip():
    pytest.skip("DATABASE_URL is required for integration tests", allow_module_level=True)

from main import app  # noqa: E402


def _reset_db() -> None:
    init_database()
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("TRUNCATE TABLE audit_logs, refresh_tokens, tasks, users RESTART IDENTITY CASCADE")
        cursor.close()
        connection.commit()

def _fetch_logs(action: str) -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT action, success, status_code, actor_user_id, resource_type, resource_id, details_json
            FROM audit_logs
            WHERE action = %s
            ORDER BY id
            """,
            (action,),
        )
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        return rows


def test_auth_events_are_audited() -> None:
    _reset_db()
    with TestClient(app) as client:
        register_response = client.post(
            "/auth/register",
            json={"username": "alice", "password": "password123"},
        )
        assert register_response.status_code == 201

        failed_login = client.post(
            "/auth/login",
            json={"username": "alice", "password": "bad-password"},
        )
        assert failed_login.status_code == 401

        login_response = client.post(
            "/auth/login",
            json={"username": "alice", "password": "password123"},
        )
        assert login_response.status_code == 200

        refresh_response = client.post(
            "/auth/refresh",
            json={"refresh_token": login_response.json()["refresh_token"]},
        )
        assert refresh_response.status_code == 200

    register_logs = _fetch_logs("auth.register")
    assert len(register_logs) == 1
    assert register_logs[0]["success"] is True
    assert register_logs[0]["status_code"] == 201

    login_logs = _fetch_logs("auth.login")
    assert len(login_logs) == 2
    assert login_logs[0]["success"] is False
    assert login_logs[0]["status_code"] == 401
    assert login_logs[1]["success"] is True
    assert login_logs[1]["status_code"] == 200

    failed_details = json.loads(login_logs[0]["details_json"])
    assert failed_details["reason"] == "invalid_credentials"
    assert "password" not in failed_details

    refresh_logs = _fetch_logs("auth.refresh")
    assert len(refresh_logs) == 1
    assert refresh_logs[0]["success"] is True
    assert refresh_logs[0]["status_code"] == 200


def test_task_mutation_events_are_audited() -> None:
    _reset_db()
    with TestClient(app) as client:
        create_response = client.post(
            "/tasks",
            json={"title": "Write tests", "description": "Audit logging"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        update_response = client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
        )
        assert update_response.status_code == 200

        delete_response = client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

        missing_update = client.patch("/tasks/999999", json={"status": "done"})
        assert missing_update.status_code == 404

    create_logs = _fetch_logs("task.create")
    assert len(create_logs) == 1
    assert create_logs[0]["success"] is True
    assert create_logs[0]["resource_type"] == "task"

    update_logs = _fetch_logs("task.update")
    assert len(update_logs) == 2
    assert update_logs[0]["success"] is True
    assert update_logs[0]["resource_id"] == str(task_id)
    assert update_logs[1]["success"] is False

    delete_logs = _fetch_logs("task.delete")
    assert len(delete_logs) == 1
    assert delete_logs[0]["success"] is True
    assert delete_logs[0]["status_code"] == 204
