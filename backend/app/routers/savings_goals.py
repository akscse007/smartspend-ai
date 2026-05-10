from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SavingsGoal
from app.repositories.savings_goal_repository import SavingsGoalRepository
from app.schemas import ApiMessage, SavingsGoalCreateIn, SavingsGoalOut, SavingsGoalProgressIn
from app.security.auth import AuthUser, get_current_user
from app.services.savings_goal_service import goal_to_response, notify_savings_milestone

router = APIRouter(prefix="/savings-goals", tags=["savings-goals"])


@router.post("", response_model=SavingsGoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: SavingsGoalCreateIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = SavingsGoalRepository(db)
    goal = SavingsGoal(
        user_id=user.user_id,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
        current_saved=payload.current_saved,
    )
    created = repo.create(goal)
    return goal_to_response(db, created)


@router.get("", response_model=list[SavingsGoalOut])
def list_goals(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = SavingsGoalRepository(db)
    rows = repo.list_by_user(user.user_id, limit=limit, offset=offset)
    return [goal_to_response(db, row) for row in rows]


@router.patch("/{goal_id}/progress", response_model=SavingsGoalOut)
def update_goal_progress(
    goal_id: int,
    payload: SavingsGoalProgressIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = SavingsGoalRepository(db)
    goal = repo.get_by_id(user.user_id, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")

    previous_saved = float(goal.current_saved)
    goal.current_saved = payload.current_saved
    db.commit()
    db.refresh(goal)

    notify_savings_milestone(db, goal, previous_saved)
    return goal_to_response(db, goal)


@router.delete("/{goal_id}", response_model=ApiMessage)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = SavingsGoalRepository(db)
    goal = repo.get_by_id(user.user_id, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Savings goal not found")
    repo.delete(goal)
    return {"message": "Savings goal deleted", "timestamp": datetime.utcnow()}
