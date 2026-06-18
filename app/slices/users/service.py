    

from typing import List

from app.core.models import User
from app.slices.users.repository import UserRepository

class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    def list_all(self) -> List[User]:
        return self._repository.list_all()