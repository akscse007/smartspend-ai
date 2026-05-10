from collections import defaultdict

from app.models import Transaction


def build_budget_recommendations(transactions: list[Transaction]) -> list[dict]:
    expenses = [tx for tx in transactions if not tx.is_income]
    if not expenses:
        return []

    latest_month = max(tx.date for tx in expenses).replace(day=1)
    months = []
    cursor = latest_month
    for _ in range(3):
        months.append(cursor.strftime("%Y-%m"))
        prev_month = cursor.month - 1 or 12
        prev_year = cursor.year - 1 if cursor.month == 1 else cursor.year
        cursor = cursor.replace(year=prev_year, month=prev_month)

    category_monthly: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    category_total: dict[str, float] = defaultdict(float)

    for tx in expenses:
        mk = tx.date.strftime("%Y-%m")
        category_monthly[tx.category][mk] += tx.amount_inr
        category_total[tx.category] += tx.amount_inr

    total_spend = sum(category_total.values())
    recommendations: list[dict] = []

    for category, value in sorted(category_total.items(), key=lambda x: x[1], reverse=True):
        share = (value / total_spend) * 100 if total_spend else 0
        if share < 20:
            continue

        three_month_avg = sum(category_monthly[category].get(m, 0.0) for m in months) / 3
        recommended = max(three_month_avg * 0.9, 0.0)
        savings = max(value - recommended, 0.0)

        recommendations.append(
            {
                "category": category,
                "current_spend": round(value, 2),
                "recommended_budget": round(recommended, 2),
                "potential_savings": round(savings, 2),
                "advice": f"Cap {category} to INR {recommended:.0f} next month and shift excess to savings.",
            }
        )

    return recommendations
