from typing import List

from app.core.exceptions import InvalidTaskSearchError, TaskNotFoundByNameError, TaskNotFoundError
from app.core.models import Task
from app.slices.tasks.models import TaskCreateRequest, TaskUpdateRequest
from app.slices.tasks.repository import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository):
        self._repository = repository

    def create_task(self, payload: TaskCreateRequest, user_id: int = 0) -> Task:
        if user_id:
            return self._repository.create(
                title=payload.title,
                description=payload.description,
                user_id=user_id,
            )
        return self._repository.create(
            title=payload.title,
            description=payload.description,
        )

    def list_tasks(self, user_id: int = 0) -> List[Task]:
        if user_id:
            return self._repository.list_all(user_id)
        return self._repository.list_all()

    def get_task(self, task_id: int, user_id: int = 0) -> Task:
        if user_id:
            task = self._repository.get_by_id(task_id, user_id)
        else:
            task = self._repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        return task

    def get_task_by_name(self, task_name: str, user_id: int = 0) -> Task:
        normalized_name = task_name.strip()
        if not normalized_name:
            raise InvalidTaskSearchError()

        if user_id:
            tasks = self._repository.list_all(user_id)
        else:
            tasks = self._repository.list_all()
        for task in tasks:
            if normalized_name.lower() in task.title.lower():
                return task
        raise TaskNotFoundByNameError(normalized_name)

    def get_tasks_by_status(self, status: str, user_id: int = 0) -> List[Task]:
        normalized_status = status.strip().lower()
        if normalized_status not in {"todo", "in_progress", "done", "archived"}:
            raise InvalidTaskSearchError()

        if user_id:
            tasks = self._repository.get_by_status(normalized_status, user_id)
        else:
            tasks = self._repository.get_by_status(normalized_status)
        return [task for task in tasks if task.status == normalized_status]

    def update_task(self, task_id: int, payload: TaskUpdateRequest, user_id: int = 0) -> Task:
        task = self.get_task(task_id, user_id)

        if payload.title is not None:
            task.title = payload.title
        if payload.description is not None:
            task.description = payload.description
        if payload.status is not None:
            task.status = payload.status

        return self._repository.update(task)

    def delete_task(self, task_id: int, user_id: int = 0) -> None:
        self.get_task(task_id, user_id)
        if user_id:
            self._repository.delete(task_id, user_id)
        else:
            self._repository.delete(task_id)
