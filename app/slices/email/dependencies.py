from app.slices.email.service import EmailService

_service = EmailService()


def get_email_service() -> EmailService:
    return _service
