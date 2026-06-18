import logging
from functools import lru_cache
from typing import List

from fastapi import APIRouter, Depends

from app.core.models import User
from app.slices.auth.dependencies import get_request_user
from app.slices.auth.models import UserResponse
from app.slices.users.repository import UserRepository
from app.slices.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger("app.api.users")

# Dependency to get UserService instance with caching
@lru_cache(maxsize=1)
def get_user_service() -> UserService:
    repository = UserRepository()
    return UserService(repository)

@router.get("", response_model=List[UserResponse])
def list_users(
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_request_user),
) -> List[UserResponse]:
    users = service.list_all()
    logger.info("list users success count=%s user_id=%s", len(users), current_user.id or 0)
    return [UserResponse.model_validate(user, from_attributes=True) for user in users]