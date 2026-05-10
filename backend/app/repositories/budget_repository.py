from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models import Budget, Transaction


class BudgetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, budget: Budget) -> Budget:
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def list_by_user(
        self,
        user_id: int,
        month: int | None = None,
        year: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Budget]:
        query = self.db.query(Budget).filter(Budget.user_id == user_id)
        if month is not None:
            query = query.filter(Budget.month == month)
        if year is not None:
            query = query.filter(Budget.year == year)
        return query.order_by(Budget.year.desc(), Budget.month.desc(), Budget.category.asc()).offset(offset).limit(limit).all()

    def get_by_id(self, user_id: int, budget_id: int) -> Budget | None:
        return self.db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()

    def get_by_unique(self, user_id: int, category: str, month: int, year: int) -> Budget | None:
        return (
            self.db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.category == category,
                Budget.month == month,
                Budget.year == year,
            )
            .first()
        )

    def delete(self, budget: Budget) -> None:
        self.db.delete(budget)
        self.db.commit()

    def spent_for_budget(self, budget: Budget) -> float:
        spent = (
            self.db.query(func.coalesce(func.sum(func.abs(Transaction.amount_inr)), 0.0))
            .filter(
                Transaction.is_income.is_(False),
                Transaction.category == budget.category,
                extract("year", Transaction.date) == budget.year,
                extract("month", Transaction.date) == budget.month,
            )
            .scalar()
        )
        return float(spent or 0.0)
