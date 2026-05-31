import json
from typing import Any, Optional

from pydantic import BaseModel

from app.core.models import AuditLog


class AuditLogResponse(BaseModel):
    id: int
    occurred_at: int
    actor_user_id: Optional[int]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    success: bool
    http_method: Optional[str]
    path: Optional[str]
    status_code: Optional[int]
    client_ip: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[str]
    details: Optional[dict[str, Any]]

    @classmethod
    def from_domain(cls, record: AuditLog) -> "AuditLogResponse":
        details = None
        if record.details_json:
            try:
                parsed = json.loads(record.details_json)
                if isinstance(parsed, dict):
                    details = parsed
            except json.JSONDecodeError:
                details = None

        return cls(
            id=record.id,
            occurred_at=record.occurred_at,
            actor_user_id=record.actor_user_id,
            action=record.action,
            resource_type=record.resource_type,
            resource_id=record.resource_id,
            success=record.success,
            http_method=record.http_method,
            path=record.path,
            status_code=record.status_code,
            client_ip=record.client_ip,
            user_agent=record.user_agent,
            request_id=record.request_id,
            details=details,
        )


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int
