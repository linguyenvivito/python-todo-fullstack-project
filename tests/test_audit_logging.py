import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import init_database


TEST_DB = Path(__file__).with_name("test_audit.db")
os.environ.pop("DATABASE_URL", None)
os.environ["SQLITE_DB_PATH"] = str(TEST_DB)

from main import app  # noqa: E402


def _reset_db() -> None:
    init_database()
    with sqlite3.connect(TEST_DB) as connection:
        connection.execute("DELETE FROM audit_logs")
        connection.execute("DELETE FROM refresh_tokens")
        connection.execute("DELETE FROM tasks")
        connection.execute("DELETE FROM users")
        connection.commit()


@contextmanager
def _use_audit_test_db():
    previous_db = os.environ.get("SQLITE_DB_PATH")
    os.environ["SQLITE_DB_PATH"] = str(TEST_DB)
    try:
        yield
    finally:
        if previous_db is None:
            os.environ.pop("SQLITE_DB_PATH", None)
        else:
            os.environ["SQLITE_DB_PATH"] = previous_db


def _fetch_logs(action: str) -> list[sqlite3.Row]:
    with sqlite3.connect(TEST_DB) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT action, success, status_code, actor_user_id, resource_type, resource_id, details_json
            FROM audit_logs
            WHERE action = ?
            ORDER BY id
            """,
            (action,),
        ).fetchall()


def test_auth_events_are_audited() -> None:
    with _use_audit_test_db():
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
        assert register_logs[0]["success"] == 1
        assert register_logs[0]["status_code"] == 201

        login_logs = _fetch_logs("auth.login")
        assert len(login_logs) == 2
        assert login_logs[0]["success"] == 0
        assert login_logs[0]["status_code"] == 401
        assert login_logs[1]["success"] == 1
        assert login_logs[1]["status_code"] == 200

        failed_details = json.loads(login_logs[0]["details_json"])
        assert failed_details["reason"] == "invalid_credentials"
        assert "password" not in failed_details

        refresh_logs = _fetch_logs("auth.refresh")
        assert len(refresh_logs) == 1
        assert refresh_logs[0]["success"] == 1
        assert refresh_logs[0]["status_code"] == 200


def test_task_mutation_events_are_audited() -> None:
    with _use_audit_test_db():
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
        assert create_logs[0]["success"] == 1
        assert create_logs[0]["resource_type"] == "task"

        update_logs = _fetch_logs("task.update")
        assert len(update_logs) == 2
        assert update_logs[0]["success"] == 1
        assert update_logs[0]["resource_id"] == str(task_id)
        assert update_logs[1]["success"] == 0

        delete_logs = _fetch_logs("task.delete")
        assert len(delete_logs) == 1
        assert delete_logs[0]["success"] == 1
        assert delete_logs[0]["status_code"] == 204
