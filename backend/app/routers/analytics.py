from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction
from app.repositories.analytics_repository import AnalyticsRepository
from app.schemas import CashflowCalendarOut, FeedbackInsightsOut, MerchantIntelligenceOut, SavingsForecastOut, WhatIfSimulationIn, WhatIfSimulationOut
from app.security.auth import AuthUser, get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def analytics_overview(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    service = AnalyticsService(db, user.user_id)
    snapshot = service.dashboard_snapshot()
    return {
        "overview": snapshot,
        "category_distribution": service.category_totals(*map(int, snapshot["month"].split("-"))),
        "monthly_category_spending": service.monthly_category_spending(),
        "forecast": service.forecast(),
        "duplicates": service.duplicate_transactions(),
        "subscriptions": service.subscriptions(),
        "insights": service.generate_insights(),
    }


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    service = AnalyticsService(db, user.user_id)
    snapshot = service.dashboard_snapshot()

    largest_tx = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.user_id, Transaction.is_income.is_(False))
        .order_by(func.abs(Transaction.amount_inr).desc())
        .first()
    )
    top_merchants = (
        db.query(Transaction.merchant, func.count(Transaction.id).label("count"))
        .filter(Transaction.user_id == user.user_id, Transaction.is_income.is_(False))
        .group_by(Transaction.merchant)
        .order_by(func.count(Transaction.id).desc())
        .limit(5)
        .all()
    )
    daily_spending = (
        db.query(Transaction.date, func.sum(func.abs(Transaction.amount_inr)).label("amount"))
        .filter(Transaction.user_id == user.user_id, Transaction.is_income.is_(False))
        .group_by(Transaction.date)
        .order_by(Transaction.date.asc())
        .all()
    )

    monthly = AnalyticsRepository(db).monthly_income_expense(user.user_id)
    latest = monthly[-1] if monthly else {"month": datetime.utcnow().strftime("%Y-%m"), "income": 0.0, "expense": 0.0}
    return {
        "month": latest["month"],
        "total_monthly_spending": round(latest["expense"], 2),
        "total_monthly_income": round(latest["income"], 2),
        "net_savings": round(latest["income"] - latest["expense"], 2),
        "highest_category": snapshot["top_category"],
        "largest_transaction": {
            "description": largest_tx.description,
            "amount_inr": round(abs(largest_tx.amount_inr), 2),
        }
        if largest_tx
        else None,
        "top_merchants": [{"merchant": merchant, "count": count} for merchant, count in top_merchants],
        "daily_spending_heatmap": [{"date": row.date.isoformat(), "amount": round(float(row.amount or 0.0), 2)} for row in daily_spending],
        "remaining_budget": snapshot["remaining_budget"],
        "monthly_budget": snapshot["monthly_budget"],
    }


@router.get("/categories")
def categories(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    latest = AnalyticsRepository(db).latest_expense_month(user.user_id)
    if latest is None:
        return []
    return AnalyticsService(db, user.user_id).category_totals(year=latest[0], month=latest[1])


@router.get("/monthly-trend")
def monthly_trend(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = AnalyticsRepository(db)
    return [
        {
            "month": row["month"],
            "income": round(row["income"], 2),
            "expense": round(row["expense"], 2),
        }
        for row in repo.monthly_income_expense(user.user_id)
    ]


@router.get("/monthly-summary")
def monthly_summary(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = AnalyticsRepository(db)
    data = repo.monthly_income_expense(user.user_id)
    return [
        {
            "month": row["month"],
            "total_income": round(row["income"], 2),
            "total_expense": round(row["expense"], 2),
            "net_savings": round(row["income"] - row["expense"], 2),
        }
        for row in data
    ]


@router.get("/category-distribution")
def category_distribution(
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    repo = AnalyticsRepository(db)
    if year is None or month is None:
        latest = repo.latest_expense_month(user.user_id)
        if latest is None:
            return {"month": None, "distribution": []}
        year, month = latest

    data = AnalyticsService(db, user.user_id).category_totals(year=year, month=month)
    return {"month": f"{year:04d}-{month:02d}", "distribution": data}


@router.get("/income-vs-expense")
def income_vs_expense(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsRepository(db).monthly_income_expense(user.user_id)


@router.get("/savings-rate")
def savings_rate(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    series = []
    for row in AnalyticsRepository(db).monthly_income_expense(user.user_id):
        income = row["income"]
        expense = row["expense"]
        rate = ((income - expense) / income) * 100 if income > 0 else 0.0
        series.append(
            {
                "month": row["month"],
                "income": round(income, 2),
                "expense": round(expense, 2),
                "savings_rate": round(rate, 2),
            }
        )
    return series


@router.get("/forecast")
def forecast(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).forecast()


@router.get("/savings-forecast", response_model=SavingsForecastOut)
def savings_forecast(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).savings_forecast()


@router.get("/cashflow-calendar", response_model=CashflowCalendarOut)
def cashflow_calendar(
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).cashflow_calendar(days=days)


@router.get("/merchant-intelligence", response_model=MerchantIntelligenceOut)
def merchant_intelligence(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).merchant_intelligence()


@router.post("/what-if", response_model=WhatIfSimulationOut)
def what_if(
    payload: WhatIfSimulationIn,
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).what_if_simulation(
        category=payload.category,
        spend_delta=payload.spend_delta,
        extra_savings=payload.extra_savings,
    )


@router.get("/feedback-insights", response_model=FeedbackInsightsOut)
def feedback_insights(
    db: Session = Depends(get_db),
    user: AuthUser = Depends(get_current_user),
):
    return AnalyticsService(db, user.user_id).feedback_insights()
