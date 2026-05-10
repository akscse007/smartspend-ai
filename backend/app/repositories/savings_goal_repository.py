from sqlalchemy.orm import Session

from app.models import SavingsGoal


class SavingsGoalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, goal: SavingsGoal) -> SavingsGoal:
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def list_by_user(self, user_id: int, limit: int = 100, offset: int = 0) -> list[SavingsGoal]:
        return (
            self.db.query(SavingsGoal)
            .filter(SavingsGoal.user_id == user_id)
            .order_by(SavingsGoal.target_date.asc(), SavingsGoal.id.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_id(self, user_id: int, goal_id: int) -> SavingsGoal | None:
        return self.db.query(SavingsGoal).filter(SavingsGoal.user_id == user_id, SavingsGoal.id == goal_id).first()

    def delete(self, goal: SavingsGoal) -> None:
        self.db.delete(goal)
        self.db.commit()
