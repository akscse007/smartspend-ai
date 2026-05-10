import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.ml.categories import normalize_category_label
from app.ml.merchant_rules import logo_for_merchant
from app.models import CategoryOverride, Transaction
from app.repositories.ai_repository import AIRepository
from app.repositories.notification_repository import NotificationRepository
from app.schemas import CategoryOverrideIn, ManualTransactionIn, TransactionOut, UploadResponse
from app.security.auth import AuthUser, get_current_user
from app.services.anomaly_service import is_anomalous_expense
from app.services.categorization_service import CategorizationService
from app.services.notification_service import notify_anomaly, notify_budget_usage_for_category
from app.services.subscription_service import detect_subscriptions
from app.utils.text_cleaner import parse_amount, parse_date, source_hash

router = APIRouter(prefix="", tags=["transactions"])
service = CategorizationService(settings.model_path)


def _transaction_payload(tx: Transaction) -> dict:
    confidence = float(tx.prediction_confidence or 0.0)
    return {
        "id": tx.id,
        "date": tx.date,
        "description": tx.description,
        "merchant": tx.merchant,
        "amount": float(tx.amount),
        "currency": tx.currency,
        "amount_inr": float(tx.amount_inr),
        "category": tx.category,
        "prediction_confidence": confidence,
        "is_income": tx.is_income,
        "is_subscription": tx.is_subscription,
        "anomaly_flag": tx.anomaly_flag,
        "recurrence": tx.recurrence,
        "merchant_logo_url": logo_for_merchant(tx.merchant),
        "low_confidence": confidence < 0.6,
    }


def _history_rows(db: Session) -> list[dict]:
    raise RuntimeError("Use _history_rows_for_user instead.")


def _history_rows_for_user(db: Session, user_id: int) -> list[dict]:
    return AIRepository(db).prediction_history(user_id)


def create_transaction(
    db: Session,
    user_id: int,
    raw_date: str,
    description: str,
    raw_amount: str,
) -> tuple[Transaction | None, str]:
    try:
        tx_date = parse_date(raw_date)
        amount, currency, amount_inr = parse_amount(raw_amount)
    except Exception:
        return None, "invalid"

    tx_hash = source_hash(tx_date, description, amount_inr)
    if db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.source_hash == tx_hash).first():
        return None, "duplicate"

    prediction = service.predict(
        description=description,
        amount=amount_inr,
        history_rows=_history_rows_for_user(db, user_id),
    )
    category = normalize_category_label(prediction["predicted_category"]) if prediction["predicted_category"] != "Uncertain" else "Uncertain"
    is_income = amount_inr < 0

    anomaly_flag = False
    if not is_income:
        anomaly_flag = is_anomalous_expense(
            db,
            user_id=user_id,
            tx_date=tx_date,
            category=category,
            amount_inr=amount_inr,
        )

    tx = Transaction(
        user_id=user_id,
        date=tx_date,
        description=description,
        clean_description=prediction["features"].get("text", prediction["merchant"]),
        merchant=prediction["merchant"],
        amount=amount,
        currency=currency,
        amount_inr=amount_inr,
        category=category,
        prediction_confidence=float(prediction["confidence"]),
        is_income=is_income,
        anomaly_flag=anomaly_flag,
        source_hash=tx_hash,
    )
    db.add(tx)
    return tx, "ok"


def _finalize_inserted_transactions(db: Session, inserted: list[Transaction], user: AuthUser) -> list[dict]:
    if not inserted:
        return []

    for tx in inserted:
        db.refresh(tx)

    flags = detect_subscriptions(db.query(Transaction).filter(Transaction.user_id == user.user_id).all())
    for tx in inserted:
        if tx.id in flags:
            tx.is_subscription = True
            tx.recurrence = flags[tx.id]["recurrence"]
    db.commit()

    notification_repo = NotificationRepository(db)
    for tx in inserted:
        notify_anomaly(notification_repo, user.user_id, tx)
        if not tx.is_income:
            notify_budget_usage_for_category(db, user.user_id, tx.category, tx.date)

    return [_transaction_payload(tx) for tx in inserted]


async def _handle_upload(
    file: UploadFile,
    db: Session,
    user: AuthUser,
) -> UploadResponse:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    content = (await file.read()).decode("utf-8-sig")
    if not content.strip():
        raise HTTPException(status_code=400, detail="CSV is empty.")

    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV headers missing")

    required = {"Date", "Description", "Amount"}
    normalized_headers = {header.strip() for header in reader.fieldnames if header}
    if not required.issubset(normalized_headers):
        raise HTTPException(status_code=400, detail="CSV columns must include: Date, Description, Amount")

    inserted: list[Transaction] = []
    duplicate_count = 0
    for record in reader:
        raw_date = (record.get("Date") or "").strip()
        description = (record.get("Description") or "").strip()
        raw_amount = (record.get("Amount") or "").strip()
        if not (raw_date and description and raw_amount):
            continue

        tx, status = create_transaction(db, user.user_id, raw_date, description, raw_amount)
        if tx is None:
            if status == "duplicate":
                duplicate_count += 1
            continue
        inserted.append(tx)

    db.commit()
    payload = _finalize_inserted_transactions(db, inserted, user)
    return UploadResponse(inserted_count=len(inserted), duplicate_count=duplicate_count, transactions=payload)


@router.post("/upload", response_model=UploadResponse)
async def upload_transactions(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return await _handle_upload(file=file, db=db, user=user)


@router.post("/upload-csv", response_model=UploadResponse)
async def upload_transactions_compat(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return await _handle_upload(file=file, db=db, user=user)


@router.post("/transactions", response_model=TransactionOut)
def add_transaction(
    payload: ManualTransactionIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    tx, status = create_transaction(db, user.user_id, payload.date, payload.description.strip(), str(payload.amount))
    if tx is None:
        raise HTTPException(status_code=400, detail="Invalid data or duplicate transaction.")

    db.commit()
    response_rows = _finalize_inserted_transactions(db, [tx], user)
    return response_rows[0]


@router.get("/transactions", response_model=list[TransactionOut])
def get_transactions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    confidence_lt: float | None = Query(default=None, ge=0.0, le=1.0),
    sort_by: str = Query(default="date", pattern="^(date|amount|confidence)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    query = db.query(Transaction)
    query = query.filter(Transaction.user_id == user.user_id)

    if search:
        needle = f"%{search.strip()}%"
        query = query.filter(or_(Transaction.description.ilike(needle), Transaction.merchant.ilike(needle)))
    if category:
        query = query.filter(Transaction.category == category)
    if confidence_lt is not None:
        query = query.filter(Transaction.prediction_confidence < confidence_lt)

    sort_column = {
        "date": Transaction.date,
        "amount": Transaction.amount_inr,
        "confidence": Transaction.prediction_confidence,
    }[sort_by]
    order = asc(sort_column) if sort_order == "asc" else desc(sort_column)
    rows = query.order_by(order, desc(Transaction.id)).offset(offset).limit(limit).all()
    return [_transaction_payload(row) for row in rows]


@router.patch("/transactions/{transaction_id}/override", response_model=TransactionOut)
def override_category(
    transaction_id: int,
    payload: CategoryOverrideIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user.user_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    old = tx.category
    tx.category = normalize_category_label(payload.new_category)
    tx.prediction_confidence = max(float(tx.prediction_confidence or 0.0), 0.99)
    db.add(
        CategoryOverride(
            transaction_id=tx.id,
            previous_category=old,
            new_category=tx.category,
            reason=payload.reason,
        )
    )
    db.commit()
    db.refresh(tx)

    if not tx.is_income:
        notify_budget_usage_for_category(db, user.user_id, tx.category, tx.date)
    return _transaction_payload(tx)
