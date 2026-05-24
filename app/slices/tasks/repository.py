from typing import List, Optional

from app.core.database import get_connection, init_database
from app.core.models import Task, TaskStatus


class TaskRepository:
    def __init__(self):
        init_database()

    @staticmethod
    def _row_to_task(row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
        )

    def create(self, title: str, description: Optional[str] = None) -> Task:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
                (title, description, TaskStatus.TODO.value),
            )
            connection.commit()
            task_id = cursor.lastrowid

        return Task(
            id=task_id or 0,
            title=title,
            description=description,
            status=TaskStatus.TODO,
        )

    def list_all(self) -> List[Task]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, title, description, status FROM tasks ORDER BY id"
            ).fetchall()

        return [self._row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int) -> Optional[Task]:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, title, description, status FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_task(row)

    def update(self, task: Task) -> Task:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, status = ?
                WHERE id = ?
                """,
                (task.title, task.description, task.status.value, task.id),
            )
            connection.commit()
        return task

    def delete(self, task_id: int) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            connection.commit()
