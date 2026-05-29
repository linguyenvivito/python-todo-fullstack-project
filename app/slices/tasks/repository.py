from typing import Any, List, Optional, cast

try:
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    dict_row = None

from app.core.database import get_connection, init_database, use_postgres
from app.core.models import Task, TaskStatus


class TaskRepository:
    def __init__(self):
        init_database()

    @staticmethod
    def _row_to_task(row) -> Task:
        user_id = None
        if hasattr(row, "keys") and "user_id" in row.keys():
            user_id = row["user_id"]

        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
            user_id=user_id,
        )

    def create(self, title: str, description: Optional[str] = None, user_id: int = 0) -> Task:
        with get_connection() as connection:
            if use_postgres():
                if dict_row is None:
                    raise RuntimeError(
                        "PostgreSQL mode requires psycopg to be installed."
                    )

                pg_connection = cast(Any, connection)
                cursor = pg_connection.cursor(row_factory=dict_row)
                try:
                    cursor.execute(
                        """
                        INSERT INTO tasks (title, description, status, user_id)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (title, description, TaskStatus.TODO.value, user_id),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise RuntimeError("INSERT did not return a task id")
                    task_id = int(row["id"])
                finally:
                    cursor.close()
            else:
                cursor = connection.execute(
                    "INSERT INTO tasks (title, description, status, user_id) VALUES (?, ?, ?, ?)",
                    (title, description, TaskStatus.TODO.value, user_id),
                )
                task_id = int(cast(Any, cursor).lastrowid or 0)
            connection.commit()

        return Task(
            id=task_id or 0,
            title=title,
            description=description,
            status=TaskStatus.TODO,
            user_id=user_id,
        )

    def list_all(self, user_id: int = 0) -> List[Task]:
        with get_connection() as connection:
            if use_postgres():
                if dict_row is None:
                    raise RuntimeError(
                        "PostgreSQL mode requires psycopg to be installed."
                    )

                pg_connection = cast(Any, connection)
                cursor = pg_connection.cursor(row_factory=dict_row)
                try:
                    cursor.execute(
                        """
                        SELECT id, title, description, status, user_id
                        FROM tasks
                        WHERE user_id = %s
                        ORDER BY id
                        """,
                        (user_id,),
                    )
                    rows = cursor.fetchall()
                finally:
                    cursor.close()
            else:
                rows = connection.execute(
                    """
                    SELECT id, title, description, status, user_id
                    FROM tasks
                    WHERE user_id = ?
                    ORDER BY id
                    """,
                    (user_id,),
                ).fetchall()

        return [self._row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int, user_id: int = 0) -> Optional[Task]:
        with get_connection() as connection:
            if use_postgres():
                if dict_row is None:
                    raise RuntimeError(
                        "PostgreSQL mode requires psycopg to be installed."
                    )

                pg_connection = cast(Any, connection)
                cursor = pg_connection.cursor(row_factory=dict_row)
                try:
                    cursor.execute(
                        """
                        SELECT id, title, description, status, user_id
                        FROM tasks
                        WHERE id = %s AND user_id = %s
                        """,
                        (task_id, user_id),
                    )
                    row = cursor.fetchone()
                finally:
                    cursor.close()
            else:
                row = connection.execute(
                    """
                    SELECT id, title, description, status, user_id
                    FROM tasks
                    WHERE id = ? AND user_id = ?
                    """,
                    (task_id, user_id),
                ).fetchone()

        if row is None:
            return None
        return self._row_to_task(row)

    def get_by_status(self, status: str, user_id: int = 0) -> List[Task]:
        with get_connection() as connection:
            if use_postgres():
                if dict_row is None:
                    raise RuntimeError(
                        "PostgreSQL mode requires psycopg to be installed."
                    )

                pg_connection = cast(Any, connection)
                cursor = pg_connection.cursor(row_factory=dict_row)
                try:
                    cursor.execute(
                        """
                        SELECT id, title, description, status, user_id
                        FROM tasks
                        WHERE status = %s AND user_id = %s
                        """,
                        (status, user_id),
                    )
                    rows = cursor.fetchall()
                finally:
                    cursor.close()
            else:
                rows = connection.execute(
                    """
                    SELECT id, title, description, status, user_id
                    FROM tasks
                    WHERE status = ? AND user_id = ?
                    """,
                    (status, user_id),
                ).fetchall()

        return [self._row_to_task(row) for row in rows]

    def update(self, task: Task) -> Task:
        with get_connection() as connection:
            if use_postgres():
                cursor = connection.cursor()
                try:
                    if task.user_id is None:
                        cursor.execute(
                            """
                            UPDATE tasks
                            SET title = %s, description = %s, status = %s
                            WHERE id = %s
                            """,
                            (task.title, task.description, task.status.value, task.id),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE tasks
                            SET title = %s, description = %s, status = %s
                            WHERE id = %s AND user_id = %s
                            """,
                            (task.title, task.description, task.status.value, task.id, task.user_id),
                        )
                finally:
                    cursor.close()
            else:
                if task.user_id is None:
                    connection.execute(
                        """
                        UPDATE tasks
                        SET title = ?, description = ?, status = ?
                        WHERE id = ?
                        """,
                        (task.title, task.description, task.status.value, task.id),
                    )
                else:
                    connection.execute(
                        """
                        UPDATE tasks
                        SET title = ?, description = ?, status = ?
                        WHERE id = ? AND user_id = ?
                        """,
                        (task.title, task.description, task.status.value, task.id, task.user_id),
                    )
            connection.commit()
        return task

    def delete(self, task_id: int, user_id: int = 0) -> None:
        with get_connection() as connection:
            if use_postgres():
                cursor = connection.cursor()
                try:
                    cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
                finally:
                    cursor.close()
            else:
                connection.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            connection.commit()
