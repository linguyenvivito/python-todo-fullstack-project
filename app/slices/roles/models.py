from pydantic import BaseModel, Field, field_validator

from app.core.sanitization import sanitize_text


class RoleCreateRequest(BaseModel):
	name: str = Field(..., min_length=1, max_length=100)

	@field_validator("name", mode="before")
	@classmethod
	def sanitize_name(cls, value: str) -> str:
		return sanitize_text(value)


class RoleUpdateRequest(BaseModel):
	name: str = Field(..., min_length=1, max_length=100)

	@field_validator("name", mode="before")
	@classmethod
	def sanitize_name(cls, value: str) -> str:
		return sanitize_text(value)


class RoleResponse(BaseModel):
	id: int
	name: str
