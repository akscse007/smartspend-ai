from datetime import date, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Transaction


def is_anomalous_expense(
    db: Session,
    *,
    user_id: int,
    tx_date: date,
    category: str,
    amount_inr: float,
) -> bool:
    expense_amount = abs(amount_inr)
    if expense_amount <= 0:
        return False

    window_start = tx_date - timedelta(days=90)
    avg_recent = (
        db.query(func.avg(func.abs(Transaction.amount_inr)))
        .filter(
            Transaction.user_id == user_id,
            Transaction.is_income.is_(False),
            Transaction.category == category,
            Transaction.date >= window_start,
            Transaction.date < tx_date,
        )
        .scalar()
    )

    baseline = float(avg_recent or 0.0)
    return baseline > 0.0 and expense_amount > (2.0 * baseline)
