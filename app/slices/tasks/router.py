from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.exceptions import TaskNotFoundError
from app.slices.tasks.models import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.slices.tasks.repository import TaskRepository
from app.slices.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

_repository = TaskRepository()
_service = TaskService(_repository)


def get_task_service() -> TaskService:
    return _service


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreateRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = service.create_task(payload)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.get("", response_model=List[TaskResponse])
def list_tasks(service: TaskService = Depends(get_task_service)) -> List[TaskResponse]:
    tasks = service.list_tasks()
    return [TaskResponse.model_validate(task, from_attributes=True) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, service: TaskService = Depends(get_task_service)) -> TaskResponse:
    try:
        task = service.get_task(task_id)
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

@router.get("/name/{task_name}", response_model=TaskResponse)
def get_task_by_name(task_name: str, service: TaskService = Depends(get_task_service)) -> TaskResponse:
    try:
        task = service.get_task_by_name(task_name)
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    try:
        task = service.update_task(task_id, payload)
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, service: TaskService = Depends(get_task_service)) -> Response:
    try:
        service.delete_task(task_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
