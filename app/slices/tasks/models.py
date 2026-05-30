from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.models import TaskStatus
from app.core.sanitization import sanitize_optional_text, sanitize_text


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, value: str) -> str:
        return sanitize_text(value)

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Optional[str]) -> Optional[str]:
        return sanitize_optional_text(value)


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    status: Optional[TaskStatus] = None

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, value: Optional[str]) -> Optional[str]:
        return sanitize_optional_text(value)

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_description(cls, value: Optional[str]) -> Optional[str]:
        return sanitize_optional_text(value)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
