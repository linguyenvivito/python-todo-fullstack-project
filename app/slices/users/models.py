from typing import Optional
from pydantic import BaseModel
from app.core.sanitization import sanitize_optional_text, sanitize_text


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    