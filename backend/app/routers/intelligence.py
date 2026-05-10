from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.ml.categories import normalize_category_label
from app.models import Transaction, UserFeedback
from app.repositories.ai_repository import AIRepository
from app.schemas import CategorizeResponse, CategoryPredictionIn, FeedbackIn, FeedbackOut
from app.security.auth import AuthUser, get_current_user
from app.services.analytics_service import AnalyticsService
from app.services.categorization_service import CategorizationService
from app.services.notification_service import notify_budget_usage_for_category

router = APIRouter(prefix="", tags=["intelligence"])
service = CategorizationService(settings.model_path)


@router.post("/categorize", response_model=CategorizeResponse)
def categorize(
    payload: CategoryPredictionIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    history_rows = AIRepository(db).prediction_history(user.user_id)
    prediction = service.predict(
        description=payload.description,
        amount=payload.amount,
        history_rows=history_rows,
    )
    return {
        "description": prediction["description"],
        "predicted_category": prediction["predicted_category"],
        "confidence": prediction["confidence"],
        "merchant": prediction["merchant"],
        "merchant_logo_url": prediction.get("merchant_logo"),
        "model_source": prediction["model_source"],
    }


@router.post("/feedback", response_model=FeedbackOut)
def submit_feedback(
    payload: FeedbackIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    corrected_category = normalize_category_label(payload.corrected_category)
    predicted_category = normalize_category_label(payload.predicted_category)

    transaction = None
    if payload.transaction_id is not None:
        transaction = (
            db.query(Transaction)
            .filter(Transaction.id == payload.transaction_id, Transaction.user_id == user.user_id)
            .first()
        )
        if transaction is None:
            raise HTTPException(status_code=404, detail="Transaction not found")

        transaction.category = corrected_category
        transaction.prediction_confidence = max(float(transaction.prediction_confidence or 0.0), 0.99)
        notify_budget_usage_for_category(db, user.user_id, transaction.category, transaction.date)

    feedback = UserFeedback(
        user_id=user.user_id,
        transaction_id=payload.transaction_id,
        transaction_text=payload.transaction_text,
        predicted_category=predicted_category,
        corrected_category=corrected_category,
        created_at=datetime.utcnow(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "id": feedback.id,
        "transaction_id": feedback.transaction_id,
        "transaction_text": feedback.transaction_text,
        "predicted_category": feedback.predicted_category,
        "corrected_category": feedback.corrected_category,
        "timestamp": feedback.created_at,
    }


@router.get("/budget-insights")
def budget_insights(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).budget_insights()
