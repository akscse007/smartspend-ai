from collections import defaultdict

from app.models import Transaction


def detect_subscriptions(transactions: list[Transaction]) -> dict[int, dict]:
    grouped: dict[tuple[str, int], list[Transaction]] = defaultdict(list)

    for tx in transactions:
        amount_bucket = int(round(tx.amount_inr))
        grouped[(tx.merchant, amount_bucket)].append(tx)

    result: dict[int, dict] = {}

    for (_merchant, _bucket), rows in grouped.items():
        rows = sorted(rows, key=lambda r: r.date)
        if len(rows) < 2:
            continue

        intervals = [(rows[i].date - rows[i - 1].date).days for i in range(1, len(rows))]
        if not intervals:
            continue

        avg_interval = sum(intervals) / len(intervals)
        recurrence = "none"
        if 25 <= avg_interval <= 35:
            recurrence = "monthly"
        elif 6 <= avg_interval <= 9:
            recurrence = "weekly"

        if recurrence == "none":
            continue

        yearly_cost = rows[-1].amount_inr * (12 if recurrence == "monthly" else 52)
        for tx in rows:
            result[tx.id] = {
                "is_subscription": True,
                "recurrence": recurrence,
                "yearly_cost_estimate": round(yearly_cost, 2),
            }

    return result
