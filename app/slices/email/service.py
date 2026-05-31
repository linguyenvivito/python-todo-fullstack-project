import os
import smtplib
import time
from email.message import EmailMessage
from typing import Any, Dict, List, Tuple


class EmailConfigurationError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


class EmailService:
    EMAIL_TEMPLATES = {
        "welcome": {
            "display_name": "Welcome Email",
            "description": "Greets newly onboarded users.",
            "fields": [
                {
                    "name": "username",
                    "label": "Username",
                    "required": True,
                    "placeholder": "alice",
                },
                {
                    "name": "login_url",
                    "label": "Login URL",
                    "required": True,
                    "placeholder": "https://app.example.com/login",
                },
            ],
        },
        "password_reset": {
            "display_name": "Password Reset",
            "description": "Sends a secure password reset link.",
            "fields": [
                {
                    "name": "username",
                    "label": "Username",
                    "required": True,
                    "placeholder": "alice",
                },
                {
                    "name": "reset_link",
                    "label": "Reset Link",
                    "required": True,
                    "placeholder": "https://app.example.com/reset?token=...",
                },
                {
                    "name": "expiry_minutes",
                    "label": "Expiry (minutes)",
                    "required": False,
                    "placeholder": "30",
                },
            ],
        },
    }

    @staticmethod
    def _get_required_env(name: str) -> str:
        value = os.getenv(name, "").strip()
        if not value:
            raise EmailConfigurationError(f"Missing required SMTP setting: {name}")
        return value

    @staticmethod
    def _as_bool(value: str, default: bool) -> bool:
        normalized = (value or "").strip().lower()
        if not normalized:
            return default
        return normalized in {"1", "true", "yes", "on"}

    @staticmethod
    def _as_int(value: str, default: int) -> int:
        normalized = (value or "").strip()
        if not normalized:
            return default
        return int(normalized)

    @staticmethod
    def _as_float(value: str, default: float) -> float:
        normalized = (value or "").strip()
        if not normalized:
            return default
        return float(normalized)

    def list_templates(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for name, spec in self.EMAIL_TEMPLATES.items():
            items.append(
                {
                    "name": name,
                    "display_name": spec["display_name"],
                    "description": spec["description"],
                    "fields": spec["fields"],
                }
            )
        return items

    def _render_template(self, template_name: str, data: Dict[str, str]) -> Tuple[str, str]:
        normalized = template_name.strip().lower()
        if normalized not in self.EMAIL_TEMPLATES:
            raise EmailConfigurationError("Unsupported email template")

        if normalized == "welcome":
            username = data.get("username", "there")
            login_url = data.get("login_url", "")
            if not login_url:
                raise EmailConfigurationError("Template field 'login_url' is required")
            subject = "Welcome to Task Management API"
            body = (
                f"Hi {username},\n\n"
                "Welcome to Task Management API. Your account is ready to use.\n"
                f"Sign in here: {login_url}\n\n"
                "If you did not expect this email, please ignore it.\n"
            )
            return subject, body

        if normalized == "password_reset":
            username = data.get("username", "there")
            reset_link = data.get("reset_link", "")
            expiry_minutes = data.get("expiry_minutes", "30")
            if not reset_link:
                raise EmailConfigurationError("Template field 'reset_link' is required")
            subject = "Reset your password"
            body = (
                f"Hi {username},\n\n"
                "We received a request to reset your password.\n"
                f"Reset link: {reset_link}\n"
                f"This link expires in {expiry_minutes} minutes.\n\n"
                "If you did not request this change, you can ignore this message.\n"
            )
            return subject, body

        raise EmailConfigurationError("Unsupported email template")

    def _build_message(
        self,
        *,
        from_name: str,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{from_name} <{from_email}>" if from_name else from_email
        message["To"] = to_email
        message.set_content(body)
        return message

    def _send_with_retry(
        self,
        *,
        smtp_cls: Any,
        smtp_host: str,
        smtp_port: int,
        timeout: float,
        smtp_use_tls: bool,
        smtp_use_ssl: bool,
        smtp_username: str,
        smtp_password: str,
        message: EmailMessage,
    ) -> None:
        max_retries = max(0, self._as_int(os.getenv("SMTP_MAX_RETRIES", "2"), 2))
        backoff_seconds = max(
            0.0, self._as_float(os.getenv("SMTP_RETRY_BACKOFF_SECONDS", "0.5"), 0.5)
        )

        for attempt in range(max_retries + 1):
            try:
                with smtp_cls(smtp_host, smtp_port, timeout=timeout) as client:
                    if smtp_use_tls and not smtp_use_ssl:
                        client.starttls()
                    if smtp_username:
                        client.login(smtp_username, smtp_password)
                    client.send_message(message)
                return
            except (smtplib.SMTPException, OSError, ValueError) as exc:
                if attempt >= max_retries:
                    raise EmailDeliveryError("Failed to send email") from exc
                delay = backoff_seconds * (2**attempt)
                if delay > 0:
                    time.sleep(delay)

    def send_email(
        self,
        *,
        to_email: str,
        subject: str = "",
        body: str = "",
        template_name: str = "",
        template_data: Dict[str, str] | None = None,
    ) -> None:
        smtp_host = self._get_required_env("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587").strip())

        smtp_use_ssl = self._as_bool(os.getenv("SMTP_USE_SSL", "false"), default=False)
        smtp_use_tls = self._as_bool(os.getenv("SMTP_USE_TLS", "true"), default=True)

        smtp_username = os.getenv("SMTP_USERNAME", "").strip()
        smtp_password = os.getenv("SMTP_PASSWORD", "").strip()

        from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or smtp_username
        from_name = os.getenv("SMTP_FROM_NAME", "Task Management API").strip()
        timeout = float(os.getenv("SMTP_TIMEOUT", "10").strip())

        if not from_email:
            raise EmailConfigurationError(
                "SMTP_FROM_EMAIL or SMTP_USERNAME must be configured"
            )

        resolved_subject = subject
        resolved_body = body
        if template_name:
            resolved_subject, resolved_body = self._render_template(
                template_name, template_data or {}
            )

        message = self._build_message(
            from_name=from_name,
            from_email=from_email,
            to_email=to_email,
            subject=resolved_subject,
            body=resolved_body,
        )

        smtp_cls = smtplib.SMTP_SSL if smtp_use_ssl else smtplib.SMTP
        self._send_with_retry(
            smtp_cls=smtp_cls,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            timeout=timeout,
            smtp_use_tls=smtp_use_tls,
            smtp_use_ssl=smtp_use_ssl,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            message=message,
        )
