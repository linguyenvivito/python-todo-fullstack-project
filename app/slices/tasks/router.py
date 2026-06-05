import logging
from functools import lru_cache
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.audit import audit_service
from app.core.exceptions import InvalidTaskSearchError, TaskNotFoundByNameError, TaskNotFoundError
from app.core.models import User
from app.core.rate_limit import limiter, rate_limit
from app.slices.auth.dependencies import get_request_user
from app.slices.tasks.models import TaskCreateRequest, TaskResponse, TaskUpdateRequest
from app.slices.tasks.repository import TaskRepository
from app.slices.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger("app.api.tasks")

# Dependency to get TaskService instance with caching
@lru_cache(maxsize=1)
def get_task_service() -> TaskService:
    repository = TaskRepository()
    return TaskService(repository)


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
    audit_service.record_event(
        action="task.create",
        success=True,
        request=request,
        actor_user_id=current_user.id or None,
        resource_type="task",
        resource_id=str(task.id),
        status_code=status.HTTP_201_CREATED,
    )
    logger.info("create task success task_id=%s user_id=%s", task.id, current_user.id or 0)
    return TaskResponse.model_validate(task, from_attributes=True)


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_request_user),
) -> List[TaskResponse]:
    tasks = service.list_tasks(current_user.id) if current_user.id else service.list_tasks()
    logger.info("list tasks success count=%s user_id=%s", len(tasks), current_user.id or 0)
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
        logger.info("get task success task_id=%s user_id=%s", task_id, current_user.id or 0)
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        logger.warning("get task not found task_id=%s user_id=%s", task_id, current_user.id or 0)
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
        logger.info("get task by name success user_id=%s", current_user.id or 0)
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundByNameError as exc:
        logger.warning("get task by name not found user_id=%s", current_user.id or 0)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except InvalidTaskSearchError as exc:
        logger.warning("get task by name invalid search user_id=%s", current_user.id or 0)
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
        logger.info(
            "get tasks by status success status=%s count=%s user_id=%s",
            task_status,
            len(tasks),
            current_user.id or 0,
        )
        return [TaskResponse.model_validate(task, from_attributes=True) for task in tasks]
    except InvalidTaskSearchError as exc:
        logger.warning("get tasks by status invalid status=%s user_id=%s", task_status, current_user.id or 0)
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
        audit_service.record_event(
            action="task.update",
            success=True,
            request=request,
            actor_user_id=current_user.id or None,
            resource_type="task",
            resource_id=str(task_id),
            status_code=status.HTTP_200_OK,
            details={"has_title": payload.title is not None, "has_description": payload.description is not None, "has_status": payload.status is not None},
        )
        logger.info("update task success task_id=%s user_id=%s", task_id, current_user.id or 0)
        return TaskResponse.model_validate(task, from_attributes=True)
    except TaskNotFoundError as exc:
        audit_service.record_event(
            action="task.update",
            success=False,
            request=request,
            actor_user_id=current_user.id or None,
            resource_type="task",
            resource_id=str(task_id),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"reason": "task_not_found"},
        )
        logger.warning("update task not found task_id=%s user_id=%s", task_id, current_user.id or 0)
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
        audit_service.record_event(
            action="task.delete",
            success=True,
            request=request,
            actor_user_id=current_user.id or None,
            resource_type="task",
            resource_id=str(task_id),
            status_code=status.HTTP_204_NO_CONTENT,
        )
        logger.info("delete task success task_id=%s user_id=%s", task_id, current_user.id or 0)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except TaskNotFoundError as exc:
        audit_service.record_event(
            action="task.delete",
            success=False,
            request=request,
            actor_user_id=current_user.id or None,
            resource_type="task",
            resource_id=str(task_id),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"reason": "task_not_found"},
        )
        logger.warning("delete task not found task_id=%s user_id=%s", task_id, current_user.id or 0)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
