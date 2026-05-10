from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.notification_repository import NotificationRepository
from app.schemas import NotificationOut, NotificationReadIn
from app.security.auth import AuthUser, get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    return repo.list_by_user(user.user_id, unread_only=unread_only, limit=limit, offset=offset)


@router.patch("/{notification_id}", response_model=NotificationOut)
def mark_notification(
    notification_id: int,
    payload: NotificationReadIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = NotificationRepository(db)
    notification = repo.get_by_id(user.user_id, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = payload.is_read
    repo.save()
    db.refresh(notification)
    return notification
