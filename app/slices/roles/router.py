from functools import lru_cache
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import Response

from app.core.exceptions import RoleNotFoundError
from app.slices.roles.models import RoleCreateRequest, RoleResponse, RoleUpdateRequest
from app.slices.roles.repository import RoleRepository
from app.slices.roles.service import RoleAlreadyExistsError, RoleService

router = APIRouter(prefix="/roles", tags=["roles"])
logger = logging.getLogger("app.api.roles")


@lru_cache(maxsize=1)
def get_role_service() -> RoleService:
    repository = RoleRepository()
    return RoleService(repository)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreateRequest,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    try:
        role = service.create_role(payload.name)
        logger.info("create role success role_id=%s", role.id)
        return RoleResponse.model_validate(role, from_attributes=True)
    except RoleAlreadyExistsError as exc:
        logger.warning("create role conflict name=%s", payload.name)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("", response_model=List[RoleResponse])
def list_roles(service: RoleService = Depends(get_role_service)) -> List[RoleResponse]:
    roles = service.list_all()
    logger.info("list roles success count=%s", len(roles))
    return [RoleResponse.model_validate(role, from_attributes=True) for role in roles]


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, service: RoleService = Depends(get_role_service)) -> RoleResponse:
    try:
        role = service.get_role(role_id)
        logger.info("get role success role_id=%s", role_id)
        return RoleResponse.model_validate(role, from_attributes=True)
    except RoleNotFoundError as exc:
        logger.warning("get role not found role_id=%s", role_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    payload: RoleUpdateRequest,
    service: RoleService = Depends(get_role_service),
) -> RoleResponse:
    try:
        role = service.update_role(role_id, payload.name)
        logger.info("update role success role_id=%s", role_id)
        return RoleResponse.model_validate(role, from_attributes=True)
    except RoleNotFoundError as exc:
        logger.warning("update role not found role_id=%s", role_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RoleAlreadyExistsError as exc:
        logger.warning("update role conflict role_id=%s", role_id)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
) -> Response:
    try:
        service.delete_role(role_id)
        logger.info("delete role success role_id=%s", role_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except RoleNotFoundError as exc:
        logger.warning("delete role not found role_id=%s", role_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

