from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InstantSavingsEntry, WishlistItem
from app.repositories.instant_savings_repository import InstantSavingsRepository
from app.repositories.wishlist_repository import WishlistRepository
from app.schemas import (
    ApiMessage,
    InstantSavingsEntryCreateIn,
    InstantSavingsEntryOut,
    WishlistItemCreateIn,
    WishlistItemOut,
    WishlistItemUpdateIn,
    WishlistPlanOut,
)
from app.security.auth import AuthUser, get_current_user
from app.services.wishlist_service import WishlistPlanningService, instant_savings_entry_to_response, wishlist_item_to_response

router = APIRouter(prefix="/wishlists", tags=["wishlists"])


@router.get("/recommendations", response_model=WishlistPlanOut)
def wishlist_recommendations(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return WishlistPlanningService(db, user.user_id).recommendations()


@router.get("", response_model=list[WishlistItemOut])
def list_wishlists(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return WishlistPlanningService(db, user.user_id).list_wishlists(limit=limit, offset=offset)


@router.post("", response_model=WishlistItemOut, status_code=status.HTTP_201_CREATED)
def create_wishlist(
    payload: WishlistItemCreateIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    item = WishlistItem(
        user_id=user.user_id,
        title=payload.title.strip(),
        target_amount=payload.target_amount,
        priority=payload.priority,
        notes=payload.notes.strip() if payload.notes else None,
    )
    created = WishlistRepository(db).create(item)
    return wishlist_item_to_response(created)


@router.patch("/{wishlist_id}", response_model=WishlistItemOut)
def update_wishlist(
    wishlist_id: int,
    payload: WishlistItemUpdateIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = WishlistRepository(db)
    item = repo.get_by_id(user.user_id, wishlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    if payload.title is not None:
        item.title = payload.title.strip()
    if payload.target_amount is not None:
        item.target_amount = payload.target_amount
    if payload.priority is not None:
        item.priority = payload.priority
    if "notes" in payload.model_fields_set:
        item.notes = payload.notes.strip() if payload.notes else None

    db.commit()
    db.refresh(item)
    allocated = InstantSavingsRepository(db).allocated_totals_by_wishlist(user.user_id).get(item.id, 0.0)
    return wishlist_item_to_response(item, allocated)


@router.delete("/{wishlist_id}", response_model=ApiMessage)
def delete_wishlist(
    wishlist_id: int,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = WishlistRepository(db)
    item = repo.get_by_id(user.user_id, wishlist_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    repo.delete(item)
    return {"message": "Wishlist item deleted", "timestamp": datetime.utcnow()}


@router.post("/savings-entries", response_model=InstantSavingsEntryOut, status_code=status.HTTP_201_CREATED)
def create_instant_savings_entry(
    payload: InstantSavingsEntryCreateIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    wishlist_title_lookup: dict[int, str] = {}
    if payload.wishlist_id is not None:
        wishlist = WishlistRepository(db).get_by_id(user.user_id, payload.wishlist_id)
        if not wishlist:
            raise HTTPException(status_code=404, detail="Wishlist item not found")
        wishlist_title_lookup[wishlist.id] = wishlist.title

    entry = InstantSavingsEntry(
        user_id=user.user_id,
        wishlist_id=payload.wishlist_id,
        amount=payload.amount,
        note=payload.note.strip() if payload.note else None,
    )
    created = InstantSavingsRepository(db).create(entry)
    return instant_savings_entry_to_response(created, wishlist_title_lookup)
