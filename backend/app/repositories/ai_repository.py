from sqlalchemy.orm import Session

from app.ml.categories import normalize_category_label
from app.models import CategoryOverride, Transaction, UserFeedback


class AIRepository:
    def __init__(self, db: Session):
        self.db = db

    def training_dataset(self, user_id: int) -> list[dict]:
        transaction_rows = (
            self.db.query(
                Transaction.description,
                Transaction.clean_description,
                Transaction.merchant,
                Transaction.amount_inr,
                Transaction.category,
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.clean_description.is_not(None),
                Transaction.category.is_not(None),
            )
            .all()
        )
        feedback_rows = self.db.query(UserFeedback).filter(UserFeedback.user_id == user_id).all()

        dataset = [
            {
                "description": str(description),
                "clean_description": str(clean_description),
                "merchant": str(merchant),
                "amount_inr": float(amount_inr or 0.0),
                "category": normalize_category_label(category),
            }
            for description, clean_description, merchant, amount_inr, category in transaction_rows
            if description and category
        ]

        dataset.extend(
            {
                "description": row.transaction_text,
                "clean_description": row.transaction_text,
                "merchant": "",
                "amount_inr": 0.0,
                "category": normalize_category_label(row.corrected_category),
            }
            for row in feedback_rows
            if row.transaction_text and row.corrected_category
        )
        return dataset

    def prediction_history(self, user_id: int) -> list[dict]:
        rows = self.db.query(Transaction.merchant, Transaction.category).filter(Transaction.user_id == user_id).all()
        return [
            {
                "merchant": str(merchant),
                "category": normalize_category_label(category),
            }
            for merchant, category in rows
            if merchant and category
        ]

    def override_count(self, user_id: int) -> int:
        return int(
            self.db.query(CategoryOverride)
            .join(Transaction, Transaction.id == CategoryOverride.transaction_id)
            .filter(Transaction.user_id == user_id)
            .count()
        )

    def feedback_count(self, user_id: int) -> int:
        return int(self.db.query(UserFeedback).filter(UserFeedback.user_id == user_id).count())
