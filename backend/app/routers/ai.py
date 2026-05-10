from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories.ai_repository import AIRepository
from app.schemas import CategoryPredictionIn, CategoryPredictionOut, RetrainModelIn, RetrainModelOut
from app.security.auth import AuthUser, get_current_user
from app.security.rate_limiter import ai_rate_limit
from app.services.ai_model_service import retrain_model
from app.services.categorization_service import CategorizationService

router = APIRouter(prefix="/ai", tags=["ai"])
predict_service = CategorizationService(settings.model_path)


@router.post("/predict-category", response_model=CategoryPredictionOut, dependencies=[Depends(ai_rate_limit)])
def predict_category(
    payload: CategoryPredictionIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    history_rows = AIRepository(db).prediction_history(user.user_id)
    prediction = predict_service.predict(
        description=payload.description.strip(),
        amount=payload.amount,
        history_rows=history_rows,
    )
    return {
        "category": prediction["predicted_category"],
        "confidence": round(prediction["confidence"], 4),
        "merchant": prediction["merchant"],
        "merchant_logo_url": prediction.get("merchant_logo"),
        "model_source": prediction["model_source"],
    }


@router.post("/retrain-model", response_model=RetrainModelOut, dependencies=[Depends(ai_rate_limit)])
def retrain(
    payload: RetrainModelIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = AIRepository(db)
    dataset = repo.training_dataset(user.user_id)
    overrides_used = repo.override_count(user.user_id)
    feedback_samples = repo.feedback_count(user.user_id)

    try:
        result = retrain_model(dataset=dataset, model_path=settings.model_path, algorithm=payload.algorithm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    predict_service.reload_model()

    from app.routers.transactions import service as transaction_service

    transaction_service.reload_model()

    return {
        **result,
        "overrides_used": overrides_used,
        "feedback_samples": feedback_samples,
        "status": "retrained",
    }
