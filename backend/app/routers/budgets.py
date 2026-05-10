from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Budget
from app.repositories.budget_repository import BudgetRepository
from app.schemas import ApiMessage, BudgetBaseIn, BudgetOut, BudgetUpdateIn
from app.security.auth import AuthUser, get_current_user
from app.services.budget_service import budget_to_response, notify_if_budget_threshold_crossed

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetBaseIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = BudgetRepository(db)
    existing = repo.get_by_unique(user.user_id, payload.category, payload.month, payload.year)
    if existing:
        raise HTTPException(status_code=409, detail="Budget already exists for this category and month.")

    budget = Budget(
        user_id=user.user_id,
        category_id=payload.category_id,
        category=payload.category.strip(),
        monthly_limit=payload.monthly_limit,
        month=payload.month,
        year=payload.year,
    )
    created = repo.create(budget)
    data = budget_to_response(repo, created)
    notify_if_budget_threshold_crossed(db, data)
    return data


@router.get("", response_model=list[BudgetOut])
def list_budgets(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = BudgetRepository(db)
    rows = repo.list_by_user(user.user_id, month=month, year=year, limit=limit, offset=offset)
    return [budget_to_response(repo, row) for row in rows]


@router.get("/{budget_id}", response_model=BudgetOut)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = BudgetRepository(db)
    budget = repo.get_by_id(user.user_id, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget_to_response(repo, budget)


@router.patch("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: int,
    payload: BudgetUpdateIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = BudgetRepository(db)
    budget = repo.get_by_id(user.user_id, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    if payload.category is not None:
        budget.category = payload.category.strip()
    if payload.monthly_limit is not None:
        budget.monthly_limit = payload.monthly_limit
    if payload.month is not None:
        budget.month = payload.month
    if payload.year is not None:
        budget.year = payload.year
    if "category_id" in payload.model_fields_set:
        budget.category_id = payload.category_id

    conflict = repo.get_by_unique(user.user_id, budget.category, budget.month, budget.year)
    if conflict and conflict.id != budget.id:
        raise HTTPException(status_code=409, detail="Another budget already exists for this category and month.")

    db.commit()
    db.refresh(budget)
    data = budget_to_response(repo, budget)
    notify_if_budget_threshold_crossed(db, data)
    return data


@router.delete("/{budget_id}", response_model=ApiMessage)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = BudgetRepository(db)
    budget = repo.get_by_id(user.user_id, budget_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    repo.delete(budget)
    return {"message": "Budget deleted", "timestamp": datetime.utcnow()}
