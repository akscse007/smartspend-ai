from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.security.auth import AuthUser, get_current_user
from app.services.budget_engine import build_budget_recommendations

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get("/recommendations")
def budget_recommendations(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    txs = db.query(Transaction).filter(Transaction.user_id == user.user_id).all()
    recommendations = build_budget_recommendations(txs)
    latest_month = max((t.date for t in txs), default=datetime.utcnow().date()).strftime("%Y-%m")

    return {
        "month": latest_month,
        "recommendations": recommendations,
        "projected_savings": round(sum(item["potential_savings"] for item in recommendations), 2),
    }
