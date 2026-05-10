from datetime import date

from sqlalchemy.orm import Session

from app.models import Budget, Transaction
from app.repositories.budget_repository import BudgetRepository
from app.repositories.notification_repository import NotificationRepository
from app.services.budget_service import budget_to_response, notify_if_budget_threshold_crossed


def notify_anomaly(notification_repo: NotificationRepository, user_id: int, transaction: Transaction) -> None:
    if not transaction.anomaly_flag:
        return

    notification_repo.create(
        user_id=user_id,
        notification_type="anomaly_detected",
        message=(
            f"Anomaly detected for transaction '{transaction.description}' "
            f"(INR {abs(transaction.amount_inr):.2f}) on {transaction.date.isoformat()}."
        ),
    )

def notify_budget_usage_for_category(
    db: Session,
    user_id: int,
    category: str,
    tx_date: date,
) -> None:
    budget_repo = BudgetRepository(db)
    budgets = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.category == category,
            Budget.month == tx_date.month,
            Budget.year == tx_date.year,
        )
        .all()
    )
    for budget in budgets:
        payload = budget_to_response(budget_repo, budget)
        notify_if_budget_threshold_crossed(db, payload)
