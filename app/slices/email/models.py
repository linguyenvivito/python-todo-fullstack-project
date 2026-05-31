from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.sanitization import sanitize_text


class SendEmailRequest(BaseModel):
    to_email: str = Field(..., min_length=3, max_length=320)
    subject: Optional[str] = Field(default=None, min_length=1, max_length=160)
    body: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    template_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    template_data: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("to_email", mode="before")
    @classmethod
    def sanitize_to_email(cls, value: str) -> str:
        normalized = sanitize_text(value).lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Invalid recipient email")
        return normalized

    @field_validator("subject", mode="before")
    @classmethod
    def sanitize_subject(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return sanitize_text(value)

    @field_validator("body", mode="before")
    @classmethod
    def sanitize_body(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return sanitize_text(value)

    @field_validator("template_name", mode="before")
    @classmethod
    def sanitize_template_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return sanitize_text(value).lower()

    @field_validator("template_data", mode="before")
    @classmethod
    def sanitize_template_data(cls, value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not value:
            return {}
        sanitized: Dict[str, Any] = {}
        for key, raw in value.items():
            clean_key = sanitize_text(str(key))
            if raw is None:
                sanitized[clean_key] = ""
            else:
                sanitized[clean_key] = sanitize_text(str(raw))
        return sanitized

    @model_validator(mode="after")
    def validate_content_source(self) -> "SendEmailRequest":
        has_subject_body = bool(self.subject and self.body)
        has_template = bool(self.template_name)

        if has_subject_body == has_template:
            raise ValueError(
                "Provide either subject/body or template_name with template_data"
            )

        return self


class SendEmailResponse(BaseModel):
    detail: str


class EmailTemplateFieldResponse(BaseModel):
    name: str
    label: str
    required: bool
    placeholder: Optional[str] = None


class EmailTemplateResponse(BaseModel):
    name: str
    display_name: str
    description: str
    fields: List[EmailTemplateFieldResponse]


class EmailTemplateListResponse(BaseModel):
    items: List[EmailTemplateResponse]
