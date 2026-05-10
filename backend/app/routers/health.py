from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.security.auth import AuthUser, get_current_user

router = APIRouter(prefix="", tags=["health"])


def _calculate_health(txs: list[Transaction]) -> dict:
    if not txs:
        return {
            "score": 0.0,
            "savings_rate": 0.0,
            "overspending_frequency": 0.0,
            "emi_burden_ratio": 0.0,
            "subscription_load": 0.0,
            "tips": ["Upload transactions to get a score."],
        }

    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    categories = defaultdict(float)
    spikes = 0
    emi = 0.0
    subs = 0.0

    for tx in txs:
        mk = tx.date.strftime("%Y-%m")
        if tx.is_income:
            monthly_income[mk] += abs(tx.amount_inr)
        else:
            monthly_expense[mk] += abs(tx.amount_inr)
            categories[tx.category] += abs(tx.amount_inr)
            if tx.category == "EMI":
                emi += abs(tx.amount_inr)
            if tx.is_subscription or tx.category == "Subscriptions":
                subs += abs(tx.amount_inr)

    months = sorted(set(monthly_income.keys()) | set(monthly_expense.keys()))
    for i in range(1, len(months)):
        prev = monthly_expense.get(months[i - 1], 0.0)
        curr = monthly_expense.get(months[i], 0.0)
        if prev > 0 and curr > prev * 1.2:
            spikes += 1

    total_income = sum(monthly_income.values())
    total_expense = sum(monthly_expense.values())
    savings_rate = max((total_income - total_expense) / total_income, 0.0) if total_income else 0.0
    diversification = min(len(categories) / 8, 1.0)
    over = spikes / max(len(months) - 1, 1)
    emi_ratio = emi / total_income if total_income else 0.0
    sub_ratio = subs / total_expense if total_expense else 0.0

    score = 100 - (1 - savings_rate) * 35 - (1 - diversification) * 15 - over * 20 - min(emi_ratio, 1) * 15 - min(sub_ratio, 1) * 15
    score = max(0.0, min(100.0, round(score, 2)))

    tips = []
    if savings_rate < 0.2:
        tips.append("Increase savings rate to 20% or above.")
    if over > 0.25:
        tips.append("Control month-to-month overspending spikes.")
    if emi_ratio > 0.25:
        tips.append("Reduce EMI burden below 25% of income.")
    if sub_ratio > 0.1:
        tips.append("Trim unused subscriptions.")

    return {
        "score": score,
        "savings_rate": round(savings_rate * 100, 2),
        "overspending_frequency": round(over * 100, 2),
        "emi_burden_ratio": round(emi_ratio * 100, 2),
        "subscription_load": round(sub_ratio * 100, 2),
        "tips": tips or ["Current spending pattern is stable."],
    }


@router.get("/financial-health-score")
def financial_health_score(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    txs = db.query(Transaction).filter(Transaction.user_id == user.user_id).all()
    return _calculate_health(txs)


@router.get("/ai-summary")
def ai_summary(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    txs = db.query(Transaction).filter(Transaction.user_id == user.user_id).all()
    if not txs:
        return {"summary": "Upload transactions to generate insights."}

    monthly = defaultdict(float)
    cat = defaultdict(float)
    for tx in txs:
        if tx.is_income:
            continue
        monthly[tx.date.strftime("%Y-%m")] += abs(tx.amount_inr)
        cat[tx.category] += abs(tx.amount_inr)

    months = sorted(monthly.keys())
    current = months[-1]
    previous = months[-2] if len(months) > 1 else None
    top = max(cat, key=cat.get)
    top_value = cat[top]

    text = f"Highest spending category was {top} (INR {top_value:.0f})."
    if previous:
        previous_total, current_total = monthly[previous], monthly[current]
        if previous_total > 0:
            text += f" Total expenses changed by {((current_total - previous_total) / previous_total) * 100:.1f}% from last month."
    text += f" You can potentially save INR {top_value * 0.15:.0f} by optimizing this category."
    return {"summary": text}
