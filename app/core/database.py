import os
from contextlib import contextmanager

from typing import Any, cast

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


@contextmanager
def get_connection():
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required. Non-PostgreSQL support has been removed.")

    if psycopg is None:
        raise RuntimeError(
            "DATABASE_URL is set but psycopg is not installed. "
            "Install it with: pip install psycopg[binary]"
        )

    connection = psycopg.connect(database_url)

    try:
        yield connection
    finally:
        connection.close()


def init_database() -> None:
    with get_connection() as connection:
        cursor = cast(Any, connection).cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NULL,
                    status TEXT NOT NULL,
                    user_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    jti TEXT PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at BIGINT NOT NULL,
                    revoked_at BIGINT NULL,
                    replaced_by_jti TEXT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id BIGSERIAL PRIMARY KEY,
                    occurred_at BIGINT NOT NULL,
                    actor_user_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NULL,
                    resource_id TEXT NULL,
                    success BOOLEAN NOT NULL,
                    http_method TEXT NULL,
                    path TEXT NULL,
                    status_code INTEGER NULL,
                    client_ip TEXT NULL,
                    user_agent TEXT NULL,
                    request_id TEXT NULL,
                    details_json TEXT NULL
                );

                ALTER TABLE tasks
                ADD COLUMN IF NOT EXISTS user_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE;

                CREATE INDEX IF NOT EXISTS idx_tasks_user_id
                ON tasks(user_id);

                CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
                ON refresh_tokens(user_id);

                CREATE INDEX IF NOT EXISTS idx_audit_logs_occurred_at
                ON audit_logs(occurred_at);

                CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_user_id
                ON audit_logs(actor_user_id);

                CREATE INDEX IF NOT EXISTS idx_audit_logs_action
                ON audit_logs(action);
                """
            )
        finally:
            cursor.close()
        connection.commit()