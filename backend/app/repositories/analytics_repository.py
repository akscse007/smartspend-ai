from sqlalchemy import case, extract, func
from sqlalchemy.orm import Session

from app.models import Transaction


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def monthly_income_expense(self, user_id: int) -> list[dict]:
        year_col = extract("year", Transaction.date).label("year")
        month_col = extract("month", Transaction.date).label("month")
        rows = (
            self.db.query(
                year_col,
                month_col,
                func.sum(case((Transaction.is_income.is_(True), func.abs(Transaction.amount_inr)), else_=0.0)).label("income"),
                func.sum(case((Transaction.is_income.is_(False), func.abs(Transaction.amount_inr)), else_=0.0)).label("expense"),
            )
            .filter(Transaction.user_id == user_id)
            .group_by(year_col, month_col)
            .order_by(year_col, month_col)
            .all()
        )

        result = []
        for year, month, income, expense in rows:
            year_int = int(year)
            month_int = int(month)
            result.append(
                {
                    "month": f"{year_int:04d}-{month_int:02d}",
                    "income": float(income or 0.0),
                    "expense": float(expense or 0.0),
                }
            )
        return result

    def latest_expense_month(self, user_id: int) -> tuple[int, int] | None:
        row = (
            self.db.query(
                extract("year", Transaction.date).label("year"),
                extract("month", Transaction.date).label("month"),
            )
            .filter(Transaction.user_id == user_id, Transaction.is_income.is_(False))
            .order_by(extract("year", Transaction.date).desc(), extract("month", Transaction.date).desc())
            .first()
        )
        if row is None:
            return None
        return int(row.year), int(row.month)

    def category_distribution(self, user_id: int, year: int, month: int) -> list[dict]:
        rows = (
            self.db.query(
                Transaction.category,
                func.sum(func.abs(Transaction.amount_inr)).label("amount"),
            )
            .filter(
                Transaction.user_id == user_id,
                Transaction.is_income.is_(False),
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .group_by(Transaction.category)
            .order_by(func.sum(func.abs(Transaction.amount_inr)).desc())
            .all()
        )
        return [{"category": category, "amount": float(amount or 0.0)} for category, amount in rows]
