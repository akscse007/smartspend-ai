from sqlalchemy.orm import Session

from app.models import Budget
from app.repositories.budget_repository import BudgetRepository
from app.services.notification_dispatcher import create_user_notification


def budget_to_response(repo: BudgetRepository, budget: Budget) -> dict:
    spent = repo.spent_for_budget(budget)
    remaining = float(budget.monthly_limit) - spent
    percentage = (spent / float(budget.monthly_limit)) * 100 if budget.monthly_limit > 0 else 0.0

    return {
        "id": budget.id,
        "user_id": budget.user_id,
        "category": budget.category,
        "category_id": budget.category_id,
        "monthly_limit": float(budget.monthly_limit),
        "month": budget.month,
        "year": budget.year,
        "total_spent_per_category": round(spent, 2),
        "remaining_budget": round(remaining, 2),
        "percentage_used": round(percentage, 2),
        "overspending_flag": percentage >= 90.0,
    }


def notify_if_budget_threshold_crossed(
    db: Session,
    budget_payload: dict,
) -> None:
    threshold = _nearest_budget_threshold(budget_payload["percentage_used"])
    if threshold is None:
        return

    category = budget_payload["category"]
    period = f"{budget_payload['month']:02d}/{budget_payload['year']}"

    if threshold >= 100:
        subject = f"Budget limit reached for {category}"
        message = (
            f"Your {category} budget for {period} has reached or exceeded its monthly limit."
        )
    else:
        subject = f"Budget alert for {category}"
        message = (
            f"Your {category} budget for {period} has crossed the {threshold}% alert level."
        )

    create_user_notification(
        db,
        user_id=budget_payload["user_id"],
        notification_type=f"budget_threshold_{threshold}",
        message=message,
        email_subject=subject,
        email_message=message,
        dedupe_hours=24 * 45,
    )


def _nearest_budget_threshold(percentage_used: float) -> int | None:
    if percentage_used >= 100:
        return 100
    if percentage_used >= 90:
        return 90
    if percentage_used >= 80:
        return 80
    return None
