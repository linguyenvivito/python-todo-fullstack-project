import os
import sqlite3
from contextlib import contextmanager
from typing import Any, cast

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


def get_database_path() -> str:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.getenv("SQLITE_DB_PATH", os.path.join(project_root, "tasks.db"))


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "").strip()


def use_postgres() -> bool:
    return bool(get_database_url())


@contextmanager
def get_connection():
    if use_postgres():
        if psycopg is None:
            raise RuntimeError(
                "DATABASE_URL is set but psycopg is not installed. "
                "Install it with: pip install psycopg[binary]"
            )
        connection = psycopg.connect(get_database_url())
    else:
        connection = sqlite3.connect(get_database_path())
        connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


def init_database() -> None:
    with get_connection() as connection:
        if use_postgres():
            cursor = connection.cursor()
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

                    ALTER TABLE tasks
                    ADD COLUMN IF NOT EXISTS user_id BIGINT NULL REFERENCES users(id) ON DELETE CASCADE;

                    CREATE INDEX IF NOT EXISTS idx_tasks_user_id
                    ON tasks(user_id);
                    """
                )
            finally:
                cursor.close()
        else:
            sqlite_connection = cast(Any, connection)
            if hasattr(sqlite_connection, "executescript"):
                sqlite_connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT NULL,
                        status TEXT NOT NULL,
                        user_id INTEGER NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
                    """
                )
                pragma_result = sqlite_connection.execute("PRAGMA table_info(tasks)")
                columns = (
                    pragma_result.fetchall()
                    if pragma_result is not None and hasattr(pragma_result, "fetchall")
                    else []
                )
                column_names = {column[1] for column in columns}
                if "user_id" not in column_names:
                    sqlite_connection.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER NULL")
                sqlite_connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_tasks_user_id
                    ON tasks(user_id)
                    """
                )
            else:
                sqlite_connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT NULL,
                        status TEXT NOT NULL
                    )
                    """
                )
        connection.commit()