from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.security.auth import AuthUser, get_current_user

router = APIRouter(prefix="", tags=["alerts"])


@router.get("/alerts")
def alerts(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    txs = db.query(Transaction).filter(Transaction.user_id == user.user_id, Transaction.is_income.is_(False)).all()
    monthly_totals = defaultdict(float)
    category_monthly = defaultdict(lambda: defaultdict(float))

    for tx in txs:
        mk = tx.date.strftime("%Y-%m")
        monthly_totals[mk] += abs(tx.amount_inr)
        category_monthly[tx.category][mk] += abs(tx.amount_inr)

    months = sorted(monthly_totals.keys())
    if len(months) < 2:
        return {"alerts": []}

    current, previous = months[-1], months[-2]
    messages = []
    prev_total, curr_total = monthly_totals[previous], monthly_totals[current]

    if prev_total > 0 and curr_total > prev_total * 1.15:
        pct = ((curr_total - prev_total) / prev_total) * 100
        messages.append({"message": f"You spent {pct:.0f}% more this month.", "severity": "high"})

    for category, month_map in category_monthly.items():
        prev_cat, curr_cat = month_map.get(previous, 0.0), month_map.get(current, 0.0)
        if prev_cat > 0 and curr_cat > prev_cat * 1.2:
            pct = ((curr_cat - prev_cat) / prev_cat) * 100
            messages.append({"message": f"You spent {pct:.0f}% more on {category} this month.", "severity": "medium"})

    threshold = curr_total * 0.25 if curr_total > 0 else 0
    for tx in txs:
        if tx.date.strftime("%Y-%m") == current and abs(tx.amount_inr) > threshold and threshold > 0:
            messages.append({"message": f"Unusual large transaction detected: {tx.description} (INR {abs(tx.amount_inr):.0f}).", "severity": "high"})

    return {"month": current, "alerts": messages[:8], "generated_at": datetime.utcnow().isoformat()}
