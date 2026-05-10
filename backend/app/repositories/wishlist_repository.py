from sqlalchemy.orm import Session

from app.models import WishlistItem


class WishlistRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, item: WishlistItem) -> WishlistItem:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[WishlistItem]:
        return (
            self.db.query(WishlistItem)
            .filter(WishlistItem.user_id == user_id)
            .order_by(WishlistItem.priority.desc(), WishlistItem.target_amount.asc(), WishlistItem.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_id(self, user_id: int, wishlist_id: int) -> WishlistItem | None:
        return (
            self.db.query(WishlistItem)
            .filter(WishlistItem.user_id == user_id, WishlistItem.id == wishlist_id)
            .first()
        )

    def delete(self, item: WishlistItem) -> None:
        self.db.delete(item)
        self.db.commit()
