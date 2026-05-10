from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, notification_type: str, message: str, dedupe_hours: int = 24) -> Notification | None:
        cutoff = datetime.utcnow() - timedelta(hours=dedupe_hours)
        exists = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.type == notification_type,
                Notification.message == message,
                Notification.created_at >= cutoff,
            )
            .first()
        )
        if exists:
            return None

        entry = Notification(user_id=user_id, type=notification_type, message=message)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_by_user(self, user_id: int, unread_only: bool = False, limit: int = 50, offset: int = 0) -> list[Notification]:
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit).all()

    def get_by_id(self, user_id: int, notification_id: int) -> Notification | None:
        return self.db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()

    def save(self) -> None:
        self.db.commit()
