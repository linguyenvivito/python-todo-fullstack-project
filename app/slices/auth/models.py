from pydantic import BaseModel, Field, field_validator

from app.core.sanitization import sanitize_text


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def sanitize_username(cls, value: str) -> str:
        return sanitize_text(value)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def sanitize_username(cls, value: str) -> str:
        return sanitize_text(value)


class UserResponse(BaseModel):
    id: int
    username: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RevokeTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
