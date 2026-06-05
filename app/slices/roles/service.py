from typing import List

from app.core.exceptions import RoleNotFoundError
from app.core.models import Role
from app.slices.roles.repository import RoleRepository


class RoleAlreadyExistsError(Exception):
    pass


class RoleService:
    def __init__(self, repository: RoleRepository):
        self._repository = repository

    def list_all(self) -> List[Role]:
        return self._repository.list_all()

    def get_role(self, role_id: int) -> Role:
        role = self._repository.get_by_id(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        return role

    def create_role(self, name: str) -> Role:
        normalized_name = name.strip().lower()
        if self._repository.get_by_name(normalized_name) is not None:
            raise RoleAlreadyExistsError("Role name is already in use")
        return self._repository.create(normalized_name)

    def update_role(self, role_id: int, name: str) -> Role:
        normalized_name = name.strip().lower()
        existing = self._repository.get_by_name(normalized_name)
        if existing is not None and existing.id != role_id:
            raise RoleAlreadyExistsError("Role name is already in use")

        updated = self._repository.update(role_id, normalized_name)
        if updated is None:
            raise RoleNotFoundError(role_id)
        return updated

    def delete_role(self, role_id: int) -> None:
        deleted = self._repository.delete(role_id)
        if not deleted:
            raise RoleNotFoundError(role_id)