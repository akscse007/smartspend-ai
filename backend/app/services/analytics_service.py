from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timedelta
from math import ceil

from sqlalchemy import Numeric, cast, extract, func
from sqlalchemy.orm import Session

from app.models import Budget, SavingsGoal, Transaction, UserFeedback
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.forecast_engine import forecast_next_month_advanced, forecast_next_month_savings


class AnalyticsService:
    def __init__(self, db: Session, user_id: int) -> None:
        self.db = db
        self.user_id = user_id
        self.repo = AnalyticsRepository(db)

    def _transactions_query(self):
        return self.db.query(Transaction).filter(Transaction.user_id == self.user_id)

    def latest_month_key(self) -> str:
        monthly = self.repo.monthly_income_expense(self.user_id)
        return monthly[-1]["month"] if monthly else datetime.utcnow().strftime("%Y-%m")

    def latest_month_parts(self) -> tuple[int, int]:
        latest = self.repo.latest_expense_month(self.user_id)
        if latest is not None:
            return latest
        now = datetime.utcnow()
        return now.year, now.month

    def dashboard_snapshot(self) -> dict:
        monthly = self.repo.monthly_income_expense(self.user_id)
        latest = monthly[-1] if monthly else {"month": self.latest_month_key(), "income": 0.0, "expense": 0.0}
        current_year, current_month = map(int, latest["month"].split("-"))

        top_category_row = (
            self.db.query(Transaction.category, func.sum(func.abs(Transaction.amount_inr)).label("amount"))
            .filter(
                Transaction.user_id == self.user_id,
                Transaction.is_income.is_(False),
                extract("year", Transaction.date) == current_year,
                extract("month", Transaction.date) == current_month,
            )
            .group_by(Transaction.category)
            .order_by(func.sum(func.abs(Transaction.amount_inr)).desc())
            .first()
        )
        budgets = (
            self.db.query(Budget)
            .filter(Budget.user_id == self.user_id, Budget.month == current_month, Budget.year == current_year)
            .all()
        )
        total_budget = sum(float(item.monthly_limit) for item in budgets)
        remaining_budget = (total_budget - latest["expense"]) if total_budget else 0.0
        return {
            "month": latest["month"],
            "total_spending": round(latest["expense"], 2),
            "monthly_budget": round(total_budget, 2),
            "top_category": top_category_row[0] if top_category_row else "N/A",
            "remaining_budget": round(remaining_budget, 2),
        }

    def monthly_category_spending(self) -> list[dict]:
        year_expr = extract("year", Transaction.date)
        month_expr = extract("month", Transaction.date)
        rows = (
            self.db.query(
                year_expr.label("year"),
                month_expr.label("month"),
                Transaction.category,
                func.sum(func.abs(Transaction.amount_inr)).label("amount"),
            )
            .filter(Transaction.user_id == self.user_id, Transaction.is_income.is_(False))
            .group_by(year_expr, month_expr, Transaction.category)
            .order_by(year_expr, month_expr, Transaction.category)
            .all()
        )
        return [
            {
                "month": f"{int(year):04d}-{int(month):02d}",
                "category": category,
                "amount": round(float(amount or 0.0), 2),
            }
            for year, month, category, amount in rows
        ]

    def category_totals(self, year: int | None = None, month: int | None = None) -> list[dict]:
        query = (
            self.db.query(Transaction.category, func.sum(func.abs(Transaction.amount_inr)).label("amount"))
            .filter(Transaction.user_id == self.user_id, Transaction.is_income.is_(False))
        )
        if year is not None and month is not None:
            query = query.filter(extract("year", Transaction.date) == year, extract("month", Transaction.date) == month)
        rows = query.group_by(Transaction.category).order_by(func.sum(func.abs(Transaction.amount_inr)).desc()).all()
        return [{"category": category, "amount": round(float(amount or 0.0), 2)} for category, amount in rows]

    def duplicate_transactions(self) -> list[dict]:
        rounded_amount = cast(func.abs(Transaction.amount_inr), Numeric(12, 2))
        rows = (
            self.db.query(
                Transaction.clean_description,
                rounded_amount.label("amount"),
                func.count(Transaction.id).label("count"),
            )
            .filter(Transaction.user_id == self.user_id, Transaction.is_income.is_(False))
            .group_by(Transaction.clean_description, rounded_amount)
            .having(func.count(Transaction.id) > 1)
            .order_by(func.count(Transaction.id).desc())
            .all()
        )
        return [
            {
                "description": description,
                "amount": float(amount or 0.0),
                "count": int(count),
            }
            for description, amount, count in rows
        ]

    def subscriptions(self) -> list[dict]:
        rows = (
            self.db.query(Transaction.merchant, Transaction.recurrence, func.avg(func.abs(Transaction.amount_inr)).label("amount"))
            .filter(Transaction.user_id == self.user_id, Transaction.is_subscription.is_(True))
            .group_by(Transaction.merchant, Transaction.recurrence)
            .order_by(func.avg(func.abs(Transaction.amount_inr)).desc())
            .all()
        )
        return [
            {
                "merchant": merchant,
                "recurrence": recurrence,
                "average_amount": round(float(amount or 0.0), 2),
            }
            for merchant, recurrence, amount in rows
        ]

    def forecast(self) -> dict:
        txs = self._transactions_query().all()
        return forecast_next_month_advanced(txs)

    def savings_forecast(self) -> dict:
        txs = self._transactions_query().all()
        return forecast_next_month_savings(txs)

    def _recurrence_days(self, txs: list[Transaction], fallback: int = 30) -> int:
        if not txs:
            return fallback

        recurrence = next((tx.recurrence for tx in reversed(txs) if tx.recurrence and tx.recurrence != "none"), None)
        if recurrence == "daily":
            return 1
        if recurrence == "weekly":
            return 7
        if recurrence == "monthly":
            return 30

        dates = sorted(tx.date for tx in txs)
        if len(dates) >= 2:
            deltas = [(right - left).days for left, right in zip(dates, dates[1:]) if (right - left).days > 0]
            if deltas:
                average_gap = round(sum(deltas) / len(deltas))
                return max(7, min(average_gap, 35))
        return fallback

    def cashflow_calendar(self, days: int = 30) -> dict:
        all_rows = self._transactions_query().order_by(Transaction.date.asc(), Transaction.id.asc()).all()
        anchor_date = max((row.date for row in all_rows), default=datetime.utcnow().date())
        horizon = anchor_date + timedelta(days=days)
        events: list[dict] = []

        grouped_expenses: dict[str, list[Transaction]] = defaultdict(list)
        grouped_income: dict[str, list[Transaction]] = defaultdict(list)
        for row in all_rows:
            if row.is_income:
                grouped_income[row.merchant].append(row)
            elif row.is_subscription:
                grouped_expenses[row.merchant].append(row)

        def add_projected_events(rows_by_merchant: dict[str, list[Transaction]], kind: str) -> None:
            for merchant, txs in rows_by_merchant.items():
                if len(txs) < 1:
                    continue
                cadence_days = self._recurrence_days(txs)
                cadence = next((tx.recurrence for tx in reversed(txs) if tx.recurrence and tx.recurrence != "none"), "monthly")
                amount = round(sum(abs(float(tx.amount_inr or 0.0)) for tx in txs) / len(txs), 2)
                next_date = txs[-1].date + timedelta(days=cadence_days)
                emitted = 0
                while next_date <= anchor_date:
                    next_date += timedelta(days=cadence_days)
                while next_date <= horizon and emitted < 3:
                    events.append(
                        {
                            "date": next_date,
                            "title": merchant,
                            "amount": amount,
                            "type": kind,
                            "cadence": cadence,
                            "note": f"Projected from {len(txs)} prior {cadence} transactions.",
                        }
                    )
                    next_date += timedelta(days=cadence_days)
                    emitted += 1

        add_projected_events(grouped_expenses, "expense")
        add_projected_events({merchant: txs for merchant, txs in grouped_income.items() if len(txs) >= 2}, "income")

        goal_rows = self.db.query(SavingsGoal).filter(SavingsGoal.user_id == self.user_id).all()
        for goal in goal_rows:
            if anchor_date <= goal.target_date <= horizon:
                remaining = max(float(goal.target_amount) - float(goal.current_saved), 0.0)
                events.append(
                    {
                        "date": goal.target_date,
                        "title": "Savings goal milestone",
                        "amount": round(remaining, 2),
                        "type": "goal",
                        "cadence": None,
                        "note": f"Remaining to target: INR {remaining:.0f}.",
                    }
                )

        current_year, current_month = self.latest_month_parts()
        spent_by_category = {
            item["category"]: item["amount"]
            for item in self.category_totals(year=current_year, month=current_month)
        }
        budget_rows = (
            self.db.query(Budget)
            .filter(Budget.user_id == self.user_id, Budget.month == current_month, Budget.year == current_year)
            .all()
        )
        budget_review_date = date(current_year, current_month, 28)
        for budget in budget_rows:
            spent = spent_by_category.get(budget.category, 0.0)
            if budget.monthly_limit and spent / float(budget.monthly_limit) >= 0.85:
                events.append(
                    {
                        "date": budget_review_date,
                        "title": f"{budget.category} budget review",
                        "amount": round(max(spent - float(budget.monthly_limit), 0.0), 2),
                        "type": "budget",
                        "cadence": None,
                        "note": f"{spent / float(budget.monthly_limit):.0%} of budget used.",
                    }
                )

        events.sort(key=lambda item: (item["date"], item["type"], item["title"]))
        expected_income = round(sum(item["amount"] for item in events if item["type"] == "income"), 2)
        expected_expense = round(sum(item["amount"] for item in events if item["type"] != "income"), 2)

        return {
            "anchor_date": anchor_date,
            "window_days": days,
            "expected_income": expected_income,
            "expected_expense": expected_expense,
            "expected_net": round(expected_income - expected_expense, 2),
            "events": events[:12],
        }

    def merchant_intelligence(self) -> dict:
        year, month = self.latest_month_parts()
        rows = (
            self.db.query(
                Transaction.merchant,
                func.count(Transaction.id).label("count"),
                func.sum(func.abs(Transaction.amount_inr)).label("total"),
                func.avg(func.abs(Transaction.amount_inr)).label("avg_ticket"),
                func.max(Transaction.date).label("last_seen"),
            )
            .filter(
                Transaction.user_id == self.user_id,
                Transaction.is_income.is_(False),
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .group_by(Transaction.merchant)
            .order_by(func.sum(func.abs(Transaction.amount_inr)).desc())
            .all()
        )

        total_spend = round(sum(float(row.total or 0.0) for row in rows), 2)
        top_merchants = []
        repeat_total = 0.0
        for row in rows[:6]:
            merchant_total = round(float(row.total or 0.0), 2)
            if int(row.count or 0) >= 2:
                repeat_total += merchant_total
            share = (merchant_total / total_spend) * 100 if total_spend else 0.0
            top_merchants.append(
                {
                    "merchant": row.merchant,
                    "total_spend": merchant_total,
                    "transaction_count": int(row.count or 0),
                    "average_ticket": round(float(row.avg_ticket or 0.0), 2),
                    "share_of_spend": round(share, 2),
                    "last_seen": row.last_seen,
                }
            )

        concentration_share = round(sum(item["share_of_spend"] for item in top_merchants[:3]), 2)
        repeat_merchant_share = round((repeat_total / total_spend) * 100, 2) if total_spend else 0.0

        watchlist: list[str] = []
        if concentration_share >= 45:
            watchlist.append(f"Top 3 merchants account for {concentration_share:.0f}% of spending this month.")
        if top_merchants and top_merchants[0]["average_ticket"] >= 2500:
            watchlist.append(f"{top_merchants[0]['merchant']} has the highest average ticket size right now.")
        if repeat_merchant_share >= 35:
            watchlist.append(f"Repeat merchants drive {repeat_merchant_share:.0f}% of monthly spending.")
        if not watchlist and top_merchants:
            watchlist.append(f"{top_merchants[0]['merchant']} is the current highest-spend merchant.")

        return {
            "month": f"{year:04d}-{month:02d}",
            "total_spend": total_spend,
            "concentration_share": concentration_share,
            "repeat_merchant_share": repeat_merchant_share,
            "top_merchants": top_merchants,
            "watchlist": watchlist,
        }

    def what_if_simulation(self, category: str, spend_delta: float, extra_savings: float) -> dict:
        snapshot = self.dashboard_snapshot()
        year, month = map(int, snapshot["month"].split("-"))
        category_lookup = {
            item["category"]: item["amount"]
            for item in self.category_totals(year=year, month=month)
        }
        current_category_spend = float(category_lookup.get(category, 0.0))
        adjusted_category_spend = round(max(0.0, current_category_spend + spend_delta), 2)
        adjusted_total_spend = round(
            max(0.0, float(snapshot["total_spending"]) - current_category_spend + adjusted_category_spend),
            2,
        )
        monthly_budget = float(snapshot["monthly_budget"])
        adjusted_remaining_budget = round(monthly_budget - adjusted_total_spend, 2) if monthly_budget else 0.0
        forecast_adjusted = round(max(0.0, float(self.forecast()["predicted_amount"]) + spend_delta), 2)
        savings_impact = round((-spend_delta) + extra_savings, 2)

        summary = [
            f"Moving {category} by INR {spend_delta:.0f} changes projected monthly spend to INR {adjusted_total_spend:.0f}.",
            f"Remaining budget shifts from INR {snapshot['remaining_budget']:.0f} to INR {adjusted_remaining_budget:.0f}.",
            f"Net monthly savings improves by INR {savings_impact:.0f} when extra savings is included.",
        ]
        if adjusted_remaining_budget < 0:
            summary.append("This scenario still leaves the month over budget.")
        elif monthly_budget:
            summary.append("This scenario keeps the month within the configured budget envelope.")

        return {
            "month": snapshot["month"],
            "category": category,
            "current_category_spend": round(current_category_spend, 2),
            "adjusted_category_spend": adjusted_category_spend,
            "current_total_spend": round(float(snapshot["total_spending"]), 2),
            "adjusted_total_spend": adjusted_total_spend,
            "current_remaining_budget": round(float(snapshot["remaining_budget"]), 2),
            "adjusted_remaining_budget": adjusted_remaining_budget,
            "forecast_adjusted": forecast_adjusted,
            "savings_impact": savings_impact,
            "summary": summary,
        }

    def feedback_insights(self) -> dict:
        total_feedback = (
            self.db.query(func.count(UserFeedback.id))
            .filter(UserFeedback.user_id == self.user_id)
            .scalar()
            or 0
        )
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent_feedback = (
            self.db.query(func.count(UserFeedback.id))
            .filter(UserFeedback.user_id == self.user_id, UserFeedback.created_at >= cutoff)
            .scalar()
            or 0
        )
        low_confidence_transactions = (
            self.db.query(func.count(Transaction.id))
            .filter(Transaction.user_id == self.user_id, Transaction.prediction_confidence < 0.6)
            .scalar()
            or 0
        )
        corrected_transactions = (
            self.db.query(func.count(func.distinct(UserFeedback.transaction_id)))
            .filter(UserFeedback.user_id == self.user_id, UserFeedback.transaction_id.isnot(None))
            .scalar()
            or 0
        )
        top_corrections_rows = (
            self.db.query(
                UserFeedback.predicted_category,
                UserFeedback.corrected_category,
                func.count(UserFeedback.id).label("count"),
            )
            .filter(UserFeedback.user_id == self.user_id)
            .group_by(UserFeedback.predicted_category, UserFeedback.corrected_category)
            .order_by(func.count(UserFeedback.id).desc())
            .limit(5)
            .all()
        )
        recent_items_rows = (
            self.db.query(UserFeedback)
            .filter(UserFeedback.user_id == self.user_id)
            .order_by(UserFeedback.created_at.desc())
            .limit(5)
            .all()
        )

        guidance: list[str] = []
        if total_feedback >= 10:
            guidance.append("You have enough correction data to justify a retraining run.")
        if low_confidence_transactions >= 10:
            guidance.append("Low-confidence transactions are stacking up; review queue quality will improve retraining impact.")
        if not guidance:
            guidance.append("Keep correcting edge cases to strengthen future model performance.")

        return {
            "total_feedback": int(total_feedback),
            "recent_feedback": int(recent_feedback),
            "low_confidence_transactions": int(low_confidence_transactions),
            "corrected_transactions": int(corrected_transactions),
            "ready_for_retrain": int(total_feedback) >= 10 or int(recent_feedback) >= 5,
            "top_corrections": [
                {
                    "from_category": row.predicted_category,
                    "to_category": row.corrected_category,
                    "count": int(row.count or 0),
                }
                for row in top_corrections_rows
            ],
            "recent_items": [
                {
                    "transaction_text": row.transaction_text,
                    "predicted_category": row.predicted_category,
                    "corrected_category": row.corrected_category,
                    "timestamp": row.created_at,
                }
                for row in recent_items_rows
            ],
            "guidance": guidance,
        }

    def behavioral_budget_forecast(self) -> dict:
        year, month = self.latest_month_parts()
        monthly_expenses = (
            self.db.query(Transaction)
            .filter(
                Transaction.user_id == self.user_id,
                Transaction.is_income.is_(False),
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .order_by(Transaction.date.asc(), Transaction.id.asc())
            .all()
        )

        if monthly_expenses:
            anchor_date = max(tx.date for tx in monthly_expenses)
        else:
            today = datetime.utcnow().date()
            anchor_date = date(year, month, min(today.day, monthrange(year, month)[1]))

        days_in_month = monthrange(year, month)[1]
        elapsed_days = max(1, min(anchor_date.day, days_in_month))
        remaining_days = max(days_in_month - elapsed_days, 0)
        total_spend = round(sum(abs(float(tx.amount_inr or 0.0)) for tx in monthly_expenses), 2)
        daily_average = total_spend / elapsed_days if elapsed_days else 0.0
        projected_month_end = round(daily_average * days_in_month, 2)

        budgets = (
            self.db.query(Budget)
            .filter(Budget.user_id == self.user_id, Budget.month == month, Budget.year == year)
            .all()
        )
        category_rows = []
        alerts = []

        for budget in budgets:
            category_transactions = [tx for tx in monthly_expenses if tx.category == budget.category]
            current_spend = round(sum(abs(float(tx.amount_inr or 0.0)) for tx in category_transactions), 2)
            daily_run_rate = current_spend / elapsed_days if elapsed_days else 0.0
            projected_spend = round(daily_run_rate * days_in_month, 2)
            remaining_budget = round(float(budget.monthly_limit) - current_spend, 2)
            projected_overrun = round(max(projected_spend - float(budget.monthly_limit), 0.0), 2)

            days_to_exceed = None
            if daily_run_rate > 0 and remaining_budget > 0:
                projected_days = ceil(remaining_budget / daily_run_rate)
                if projected_days <= remaining_days:
                    days_to_exceed = projected_days
            elif remaining_budget <= 0:
                days_to_exceed = 0

            pace_ratio = (projected_spend / float(budget.monthly_limit)) * 100 if budget.monthly_limit else 0.0

            category_rows.append(
                {
                    "category": budget.category,
                    "current_spend": current_spend,
                    "daily_run_rate": round(daily_run_rate, 2),
                    "projected_spend": projected_spend,
                    "budget_limit": round(float(budget.monthly_limit), 2),
                    "remaining_budget": remaining_budget,
                    "projected_overrun": projected_overrun,
                    "days_to_exceed": days_to_exceed,
                    "pace_ratio": round(pace_ratio, 2),
                }
            )

            if days_to_exceed == 0:
                alerts.append(f"{budget.category} has already exceeded its budget.")
            elif days_to_exceed is not None:
                alerts.append(f"{budget.category} is on track to exceed budget in {days_to_exceed} days.")

        summary = [
            f"At the current pace, this month is tracking to close at INR {projected_month_end:.0f}.",
            f"Average daily spend is INR {daily_average:.0f} across {elapsed_days} observed days.",
        ]
        if alerts:
            summary.append(alerts[0])
        elif budgets:
            summary.append("Current pacing stays within budget on the observed trajectory.")

        return {
            "month": f"{year:04d}-{month:02d}",
            "anchor_date": anchor_date.isoformat(),
            "elapsed_days": elapsed_days,
            "remaining_days": remaining_days,
            "daily_average_spend": round(daily_average, 2),
            "current_total_spend": total_spend,
            "projected_month_end_spend": projected_month_end,
            "categories": sorted(category_rows, key=lambda item: item["projected_overrun"], reverse=True),
            "alerts": alerts[:5],
            "summary": summary,
        }

    def budget_insights(self) -> dict:
        snapshot = self.dashboard_snapshot()
        latest_month = snapshot["month"]
        forecast = self.forecast()
        current_year, current_month = map(int, latest_month.split("-"))
        budgets = (
            self.db.query(Budget)
            .filter(Budget.user_id == self.user_id, Budget.month == current_month, Budget.year == current_year)
            .all()
        )

        spent_by_category = {
            item["category"]: item["amount"]
            for item in self.category_totals(year=current_year, month=current_month)
        }
        alerts = []
        budget_rows = []
        for budget in budgets:
            spent = spent_by_category.get(budget.category, 0.0)
            remaining = round(float(budget.monthly_limit) - spent, 2)
            exceeded = spent > float(budget.monthly_limit)
            if exceeded:
                alerts.append(
                    f"{budget.category} spending exceeded budget by INR {round(spent - float(budget.monthly_limit), 2)}"
                )
            budget_rows.append(
                {
                    "category": budget.category,
                    "limit": round(float(budget.monthly_limit), 2),
                    "spent": round(spent, 2),
                    "remaining": remaining,
                    "percentage_used": round((spent / float(budget.monthly_limit)) * 100, 2) if budget.monthly_limit else 0.0,
                    "exceeded": exceeded,
                }
            )

        return {
            "overview": snapshot,
            "budgets": budget_rows,
            "alerts": alerts,
            "forecast": forecast,
            "savings_forecast": self.savings_forecast(),
            "behavioral_forecast": self.behavioral_budget_forecast(),
            "monthly_category_spending": self.monthly_category_spending(),
            "subscriptions": self.subscriptions(),
            "duplicates": self.duplicate_transactions(),
            "insights": self.generate_insights(),
        }

    def generate_insights(self) -> list[str]:
        monthly = self.repo.monthly_income_expense(self.user_id)
        if len(monthly) < 2:
            return ["Upload another month of transactions to unlock month-over-month insights."]

        latest = monthly[-1]
        previous = monthly[-2]
        latest_year, latest_month = map(int, latest["month"].split("-"))
        previous_year, previous_month = map(int, previous["month"].split("-"))

        latest_categories = {
            row["category"]: row["amount"]
            for row in self.category_totals(year=latest_year, month=latest_month)
        }
        previous_categories = {
            row["category"]: row["amount"]
            for row in self.category_totals(year=previous_year, month=previous_month)
        }

        insights: list[str] = []
        for category, amount in sorted(latest_categories.items(), key=lambda item: item[1], reverse=True)[:3]:
            previous_amount = previous_categories.get(category, 0.0)
            if previous_amount <= 0:
                insights.append(f"{category} appeared as a new major spend area this month at INR {amount:.0f}.")
                continue
            delta = amount - previous_amount
            change_pct = (delta / previous_amount) * 100
            direction = "more" if delta >= 0 else "less"
            insights.append(f"You spent {abs(change_pct):.0f}% {direction} on {category} this month.")

        subscriptions = self.subscriptions()
        if subscriptions:
            monthly_total = sum(
                row["average_amount"] if row["recurrence"] == "monthly" else (row["average_amount"] * 4)
                for row in subscriptions
            )
            insights.append(f"Recurring subscriptions are running at about INR {monthly_total:.0f} per month.")

        return insights[:4]
