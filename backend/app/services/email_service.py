import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.config import settings

logger = logging.getLogger(__name__)


def email_notifications_ready() -> bool:
    return bool(
        settings.email_notifications_enabled
        and settings.smtp_host
        and settings.smtp_port
        and settings.smtp_from_email
    )


def send_email(recipient_email: str, subject: str, body: str) -> bool:
    if not email_notifications_ready():
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((settings.smtp_from_name, settings.smtp_from_email or ""))
    message["To"] = recipient_email
    message.set_content(body)

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                _deliver(server, message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.ehlo()
                if settings.smtp_use_tls:
                    server.starttls()
                    server.ehlo()
                _deliver(server, message)
        return True
    except Exception:
        logger.exception("Failed to send notification email to %s", recipient_email)
        return False


def _deliver(server: smtplib.SMTP, message: EmailMessage) -> None:
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password or "")
    server.send_message(message)
