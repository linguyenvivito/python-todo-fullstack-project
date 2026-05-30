from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.exceptions import InvalidTaskSearchError, TaskNotFoundByNameError, TaskNotFoundError
from app.core.models import User
from app.core.rate_limit import limiter, rate_limit
from app.slices.auth.dependencies import get_request_user
from app.slices.tasks.models import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.slices.tasks.repository import TaskRepository
from app.slices.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

_repository = TaskRepository()
_service = TaskService(_repository)


def get_task_service() -> TaskService:
    return _service


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(rate_limit("RATE_LIMIT_TASKS_CREATE", "120/minute"))
def create_task(
    request: Request,
    payload: TaskCreateRequest,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> TaskResponse:
    task = (
        service.create_task(payload, user_id=current_user.id)
        if current_user.id
        else service.create_task(payload)
    )
    return TaskResponse.model_validate(task, from_attributes=True)


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> List[TaskResponse]:
    tasks = service.list_tasks(current_user.id) if current_user.id else service.list_tasks()
    return [TaskResponse.model_validate(task, from_attributes=True) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> TaskResponse:
    try:
        task = (
            service.get_task(task_id, user_id=current_user.id)
            if current_user.id
            else service.get_task(task_id)
        )
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

@router.get("/name/{task_name}", response_model=TaskResponse)
def get_task_by_name(
    task_name: str,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> TaskResponse:
    try:
        task = (
            service.get_task_by_name(task_name, user_id=current_user.id)
            if current_user.id
            else service.get_task_by_name(task_name)
        )
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundByNameError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTaskSearchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

# Get tasks by status
@router.get("/status/{task_status}", response_model=List[TaskResponse])
def get_tasks_by_status(
    task_status: str,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> List[TaskResponse]:
    try:
        tasks = (
            service.get_tasks_by_status(task_status, user_id=current_user.id)
            if current_user.id
            else service.get_tasks_by_status(task_status)
        )
        return [TaskResponse.model_validate(task, from_attributes=True) for task in tasks]
    except InvalidTaskSearchError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.patch("/{task_id}", response_model=TaskResponse)
@limiter.limit(rate_limit("RATE_LIMIT_TASKS_UPDATE", "180/minute"))
def update_task(
    request: Request,
    task_id: int,
    payload: TaskUpdateRequest,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> TaskResponse:
    try:
        task = (
            service.update_task(task_id, payload, user_id=current_user.id)
            if current_user.id
            else service.update_task(task_id, payload)
        )
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(rate_limit("RATE_LIMIT_TASKS_DELETE", "120/minute"))
def delete_task(
    request: Request,
    task_id: int,
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> Response:
    try:
        if current_user.id:
            service.delete_task(task_id, user_id=current_user.id)
        else:
            service.delete_task(task_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except TaskNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
