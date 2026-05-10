from sqlalchemy.orm import Session

from app.models import User
from app.repositories.notification_repository import NotificationRepository
from app.services.email_service import send_email


def create_user_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    message: str,
    *,
    email_subject: str | None = None,
    email_message: str | None = None,
    dedupe_hours: int = 24,
) -> None:
    notification = NotificationRepository(db).create(
        user_id=user_id,
        notification_type=notification_type,
        message=message,
        dedupe_hours=dedupe_hours,
    )
    if not notification or not email_subject:
        return

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        return

    send_email(
        user.email,
        email_subject,
        _build_notification_email(
            recipient_name=user.full_name,
            subject=email_subject,
            message=email_message or message,
        ),
    )


def _build_notification_email(recipient_name: str, subject: str, message: str) -> str:
    return (
        f"Hello {recipient_name},\n\n"
        f"{subject}\n\n"
        f"{message}\n\n"
        "This alert was sent to the email address linked to your Smart Budget Planner account.\n"
    )
