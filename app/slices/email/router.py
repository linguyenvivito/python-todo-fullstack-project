import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.audit import audit_service
from app.core.models import User
from app.core.rate_limit import limiter, rate_limit
from app.slices.auth.dependencies import get_current_user
from app.slices.email.dependencies import get_email_service
from app.slices.email.models import (
    EmailTemplateFieldResponse,
    EmailTemplateListResponse,
    EmailTemplateResponse,
    SendEmailRequest,
    SendEmailResponse,
)
from app.slices.email.service import EmailConfigurationError, EmailDeliveryError, EmailService

router = APIRouter(prefix="/email", tags=["email"])
logger = logging.getLogger("app.api.email")


@router.get("/templates", response_model=EmailTemplateListResponse)
def list_email_templates(
    email_service: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> EmailTemplateListResponse:
    del current_user
    items = [
        EmailTemplateResponse(
            name=item["name"],
            display_name=item["display_name"],
            description=item["description"],
            fields=[EmailTemplateFieldResponse(**field) for field in item["fields"]],
        )
        for item in email_service.list_templates()
    ]
    return EmailTemplateListResponse(items=items)


@router.post("/send", response_model=SendEmailResponse)
@limiter.limit(rate_limit("RATE_LIMIT_EMAIL_SEND", "20/minute"))
def send_email(
    request: Request,
    payload: SendEmailRequest,
    email_service: EmailService = Depends(get_email_service),
    current_user: User = Depends(get_current_user),
) -> SendEmailResponse:
    try:
        email_service.send_email(
            to_email=payload.to_email,
            subject=payload.subject or "",
            body=payload.body or "",
            template_name=payload.template_name or "",
            template_data={k: str(v) for k, v in payload.template_data.items()},
        )
    except EmailConfigurationError as exc:
        audit_service.record_event(
            action="email.send",
            success=False,
            request=request,
            actor_user_id=current_user.id,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={
                "reason": "smtp_configuration_error",
                "to_email": payload.to_email,
                "template_name": payload.template_name,
            },
        )
        logger.error("email send configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured",
        )
    except EmailDeliveryError:
        audit_service.record_event(
            action="email.send",
            success=False,
            request=request,
            actor_user_id=current_user.id,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details={
                "reason": "smtp_delivery_error",
                "to_email": payload.to_email,
                "template_name": payload.template_name,
            },
        )
        logger.warning("email send failed to=%s", payload.to_email)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send email",
        )

    audit_service.record_event(
        action="email.send",
        success=True,
        request=request,
        actor_user_id=current_user.id,
        status_code=status.HTTP_200_OK,
        details={
            "to_email": payload.to_email,
            "subject": payload.subject,
            "template_name": payload.template_name,
        },
    )
    logger.info("email send success user_id=%s to=%s", current_user.id, payload.to_email)
    return SendEmailResponse(detail="Email sent")
