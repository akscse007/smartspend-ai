from sqlalchemy import case, extract, func
from sqlalchemy.orm import Session

from app.models import SavingsGoal, Transaction
from app.services.notification_dispatcher import create_user_notification


def _avg_monthly_net_savings(db: Session, lookback_months: int = 3) -> float:
    year_col = extract("year", Transaction.date).label("year")
    month_col = extract("month", Transaction.date).label("month")
    rows = (
        db.query(
            year_col,
            month_col,
            func.sum(case((Transaction.is_income.is_(True), func.abs(Transaction.amount_inr)), else_=0.0)).label("income"),
            func.sum(case((Transaction.is_income.is_(False), func.abs(Transaction.amount_inr)), else_=0.0)).label("expense"),
        )
        .group_by(year_col, month_col)
        .order_by(year_col.desc(), month_col.desc())
        .limit(lookback_months)
        .all()
    )
    if not rows:
        return 0.0

    monthly_net = [float((row.income or 0.0) - (row.expense or 0.0)) for row in rows]
    return sum(monthly_net) / len(monthly_net)


def goal_to_response(db: Session, goal: SavingsGoal) -> dict:
    completion = (goal.current_saved / goal.target_amount) * 100 if goal.target_amount > 0 else 0.0
    remaining = max(goal.target_amount - goal.current_saved, 0.0)
    avg_net_savings = _avg_monthly_net_savings(db)

    months_remaining: float | None
    if remaining <= 0:
        months_remaining = 0.0
    elif avg_net_savings <= 0:
        months_remaining = None
    else:
        months_remaining = remaining / avg_net_savings

    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "target_amount": float(goal.target_amount),
        "target_date": goal.target_date,
        "current_saved": float(goal.current_saved),
        "completion_percentage": round(min(completion, 100.0), 2),
        "months_remaining": None if months_remaining is None else round(months_remaining, 2),
    }


def notify_savings_milestone(
    db: Session,
    goal: SavingsGoal,
    previous_saved: float,
) -> None:
    if goal.target_amount <= 0:
        return

    prev_pct = (previous_saved / goal.target_amount) * 100
    curr_pct = (goal.current_saved / goal.target_amount) * 100
    milestones = [50, 75, 90, 100]

    for milestone in milestones:
        if prev_pct < milestone <= curr_pct:
            remaining = max(float(goal.target_amount) - float(goal.current_saved), 0.0)
            if milestone >= 100:
                subject = "Savings goal reached"
                message = (
                    f"Savings goal #{goal.id} reached 100% progress. "
                    f"You saved INR {float(goal.current_saved):.2f} against your INR {float(goal.target_amount):.2f} target."
                )
            else:
                subject = "Savings target is within reach"
                message = (
                    f"Savings goal #{goal.id} reached {milestone}% progress. "
                    f"Only INR {remaining:.2f} is left before your target date of {goal.target_date.isoformat()}."
                )

            create_user_notification(
                db,
                user_id=goal.user_id,
                notification_type="savings_milestone",
                message=message,
                email_subject=subject,
                email_message=message,
                dedupe_hours=24 * 365,
            )
