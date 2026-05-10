from datetime import datetime
from itertools import combinations

from sqlalchemy.orm import Session

from app.models import InstantSavingsEntry, Transaction, WishlistItem
from app.repositories.instant_savings_repository import InstantSavingsRepository
from app.services.forecast_engine import forecast_next_month_savings


class WishlistPlanningService:
    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id
        self.savings_repo = InstantSavingsRepository(db)

    def savings_forecast(self) -> dict:
        transactions = self.db.query(Transaction).filter(Transaction.user_id == self.user_id).all()
        return forecast_next_month_savings(transactions)

    def recommendations(self, max_results: int = 6) -> dict:
        items = (
            self.db.query(WishlistItem)
            .filter(WishlistItem.user_id == self.user_id)
            .order_by(WishlistItem.priority.desc(), WishlistItem.target_amount.asc(), WishlistItem.id.asc())
            .all()
        )
        forecast = self.savings_forecast()
        current_year, current_month = self._resolve_month_parts(forecast["current_month"])
        instant_savings = self.savings_repo.current_month_total(self.user_id, current_year, current_month)
        allocated_this_month = self.savings_repo.current_month_total(
            self.user_id,
            current_year,
            current_month,
            allocated_only=True,
        )
        allocated_by_wishlist = self.savings_repo.allocated_totals_by_wishlist(self.user_id)
        current_transaction_savings = max(float(forecast["current_month_savings"]), 0.0)
        current_total_savings = current_transaction_savings + instant_savings
        current_available_savings = max(current_transaction_savings + max(instant_savings - allocated_this_month, 0.0), 0.0)
        next_cycle_capacity = current_available_savings + max(float(forecast["predicted_next_month_savings"]), 0.0)

        considered_items = items[:12]
        item_payloads = [wishlist_item_to_response(item, allocated_by_wishlist.get(item.id, 0.0)) for item in considered_items]
        immediate = self._build_combinations(item_payloads, current_available_savings, "now", max_results)
        next_cycle = self._build_combinations(item_payloads, next_cycle_capacity, "next_cycle", max_results)
        recent_entries = [
            instant_savings_entry_to_response(entry, self._wishlist_title_lookup(items))
            for entry in self.savings_repo.recent_entries(self.user_id, limit=8)
        ]

        summary: list[str] = [
            f"Transaction-based savings this month: INR {current_transaction_savings:.0f}.",
            f"Instant savings added this month: INR {instant_savings:.0f}.",
            f"Available savings left for new wishlist allocations this month: INR {current_available_savings:.0f}.",
            f"Predicted next month savings: INR {float(forecast['predicted_next_month_savings']):.0f}.",
        ]
        if not items:
            summary.append("Add wishlist items to start generating recommended bundles.")
        elif not immediate:
            summary.append("No wishlist bundle fits inside the current month's savings yet.")
        else:
            summary.append(f"{len(immediate)} combinations fit right now, ranked by priority and savings utilization.")
        if len(items) > len(considered_items):
            summary.append("Combination planning is capped to the top 12 wishlist items by priority for performance.")

        return {
            "current_month": forecast["current_month"],
            "next_month": forecast["next_month"],
            "current_month_savings": round(current_total_savings, 2),
            "current_month_transaction_savings": round(current_transaction_savings, 2),
            "current_month_instant_savings": round(instant_savings, 2),
            "current_month_allocated_savings": round(allocated_this_month, 2),
            "current_month_available_savings": round(current_available_savings, 2),
            "predicted_next_month_savings": round(float(forecast["predicted_next_month_savings"]), 2),
            "next_cycle_savings_capacity": round(next_cycle_capacity, 2),
            "wishlist_count": len(items),
            "considered_wishlist_count": len(considered_items),
            "immediately_affordable": immediate,
            "next_cycle_affordable": next_cycle,
            "recent_savings_entries": recent_entries,
            "suggestion_summary": summary,
        }

    def _build_combinations(
        self,
        items: list[dict],
        capacity: float,
        horizon: str,
        max_results: int,
    ) -> list[dict]:
        if capacity <= 0 or not items:
            return []

        rows: list[dict] = []
        for size in range(1, len(items) + 1):
            for combo in combinations(items, size):
                total_cost = round(sum(float(item["remaining_target"]) for item in combo), 2)
                if total_cost > capacity:
                    continue

                priority_score = sum(int(item["priority"]) for item in combo)
                remaining = round(capacity - total_cost, 2)
                utilization = round((total_cost / capacity) * 100, 2) if capacity else 0.0
                score = round((priority_score * 1000) + total_cost - remaining, 2)
                combo_ids = "-".join(str(item["id"]) for item in combo)
                rows.append(
                    {
                        "combo_key": f"{horizon}:{combo_ids}",
                        "horizon": horizon,
                        "items": list(combo),
                        "total_cost": total_cost,
                        "remaining_savings": remaining,
                        "utilization": utilization,
                        "priority_score": priority_score,
                        "recommended": False,
                        "summary": self._combo_summary(combo, horizon, utilization, remaining),
                        "_score": score,
                    }
                )

        rows.sort(
            key=lambda item: (
                -item["_score"],
                item["remaining_savings"],
                -len(item["items"]),
                item["combo_key"],
            )
        )
        trimmed = rows[:max_results]
        for index, row in enumerate(trimmed):
            row["recommended"] = index == 0
            row.pop("_score", None)
        return trimmed

    def _combo_summary(
        self,
        combo: tuple[dict, ...],
        horizon: str,
        utilization: float,
        remaining: float,
    ) -> str:
        titles = ", ".join(item["title"] for item in combo[:3])
        if len(combo) > 3:
            titles = f"{titles}, and {len(combo) - 3} more"
        timeline = "this month's savings" if horizon == "now" else "current plus predicted next-month savings"
        return (
            f"{titles} fits within {timeline}, uses {utilization:.0f}% of the available pool, "
            f"and leaves INR {remaining:.0f} unallocated."
        )

    def list_wishlists(self, limit: int = 100, offset: int = 0) -> list[dict]:
        rows = (
            self.db.query(WishlistItem)
            .filter(WishlistItem.user_id == self.user_id)
            .order_by(WishlistItem.priority.desc(), WishlistItem.target_amount.asc(), WishlistItem.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        allocated = self.savings_repo.allocated_totals_by_wishlist(self.user_id)
        return [wishlist_item_to_response(row, allocated.get(row.id, 0.0)) for row in rows]

    def _resolve_month_parts(self, month_key: str) -> tuple[int, int]:
        if month_key == "insufficient-data":
            now = datetime.utcnow()
            return now.year, now.month
        year, month = map(int, month_key.split("-"))
        return year, month

    def _wishlist_title_lookup(self, items: list[WishlistItem]) -> dict[int, str]:
        return {item.id: item.title for item in items}


def wishlist_item_to_response(item: WishlistItem, allocated_saved: float = 0.0) -> dict:
    target_amount = round(float(item.target_amount), 2)
    allocated = round(float(allocated_saved), 2)
    remaining = round(max(target_amount - allocated, 0.0), 2)
    completion = round(min((allocated / target_amount) * 100, 100.0), 2) if target_amount > 0 else 0.0
    return {
        "id": item.id,
        "user_id": item.user_id,
        "title": item.title,
        "target_amount": target_amount,
        "priority": item.priority,
        "notes": item.notes,
        "allocated_saved": allocated,
        "remaining_target": remaining,
        "completion_percentage": completion,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def instant_savings_entry_to_response(entry: InstantSavingsEntry, wishlist_titles: dict[int, str]) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "wishlist_id": entry.wishlist_id,
        "wishlist_title": wishlist_titles.get(entry.wishlist_id) if entry.wishlist_id is not None else None,
        "amount": round(float(entry.amount), 2),
        "note": entry.note,
        "created_at": entry.created_at,
    }
