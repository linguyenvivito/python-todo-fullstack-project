import os
import sqlite3
from contextlib import contextmanager

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
                    CREATE TABLE IF NOT EXISTS tasks (
                        id BIGSERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NULL,
                        status TEXT NOT NULL
                    )
                    """
                )
            finally:
                cursor.close()
        else:
            connection.execute(
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