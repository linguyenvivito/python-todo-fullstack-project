from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.audit import audit_service
from app.core.models import User
from app.slices.audit.models import AuditLogListResponse, AuditLogResponse
from app.slices.auth.dependencies import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    action: Optional[str] = Query(default=None, max_length=128),
    success: Optional[bool] = Query(default=None),
    actor_user_id: Optional[int] = Query(default=None, ge=1),
    occurred_from: Optional[int] = Query(default=None, ge=0),
    occurred_to: Optional[int] = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
) -> AuditLogListResponse:
    items, total = audit_service.list_events(
        action=action,
        success=success,
        actor_user_id=actor_user_id,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.from_domain(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
