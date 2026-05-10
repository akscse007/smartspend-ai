from datetime import datetime

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models import InstantSavingsEntry


class InstantSavingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, entry: InstantSavingsEntry) -> InstantSavingsEntry:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def current_month_total(self, user_id: int, year: int, month: int, *, allocated_only: bool | None = None) -> float:
        query = self.db.query(func.sum(InstantSavingsEntry.amount)).filter(
            InstantSavingsEntry.user_id == user_id,
            extract("year", InstantSavingsEntry.created_at) == year,
            extract("month", InstantSavingsEntry.created_at) == month,
        )
        if allocated_only is True:
            query = query.filter(InstantSavingsEntry.wishlist_id.isnot(None))
        elif allocated_only is False:
            query = query.filter(InstantSavingsEntry.wishlist_id.is_(None))
        return float(query.scalar() or 0.0)

    def allocated_totals_by_wishlist(self, user_id: int) -> dict[int, float]:
        rows = (
            self.db.query(InstantSavingsEntry.wishlist_id, func.sum(InstantSavingsEntry.amount))
            .filter(InstantSavingsEntry.user_id == user_id, InstantSavingsEntry.wishlist_id.isnot(None))
            .group_by(InstantSavingsEntry.wishlist_id)
            .all()
        )
        return {int(wishlist_id): round(float(total or 0.0), 2) for wishlist_id, total in rows if wishlist_id is not None}

    def recent_entries(self, user_id: int, limit: int = 10) -> list[InstantSavingsEntry]:
        return (
            self.db.query(InstantSavingsEntry)
            .filter(InstantSavingsEntry.user_id == user_id)
            .order_by(InstantSavingsEntry.created_at.desc(), InstantSavingsEntry.id.desc())
            .limit(limit)
            .all()
        )
