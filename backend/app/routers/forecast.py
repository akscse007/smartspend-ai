from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.security.auth import AuthUser, get_current_user
from app.services.forecast_engine import forecast_next_month

router = APIRouter(prefix="", tags=["forecast"])


@router.get("/forecast")
def forecast(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    txs = db.query(Transaction).filter(Transaction.user_id == user.user_id).all()
    return forecast_next_month(txs)
