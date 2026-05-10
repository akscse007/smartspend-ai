SUPPORTED_CATEGORIES = [
    "Food",
    "Transport",
    "Groceries",
    "Shopping",
    "Bills",
    "Healthcare",
    "Entertainment",
    "Travel",
    "Subscriptions",
    "Others",
]

CATEGORY_ALIASES = {
    "utilities": "Bills",
    "utility": "Bills",
    "emi": "Bills",
    "insurance": "Bills",
    "health": "Healthcare",
    "medical": "Healthcare",
    "medicine": "Healthcare",
    "education": "Others",
    "investment": "Others",
    "salary": "Others",
    "income": "Others",
    "other": "Others",
}


def normalize_category_label(label: str | None) -> str:
    raw = (label or "").strip()
    if not raw:
        return "Others"

    if raw.lower() == "uncertain":
        return "Uncertain"

    if raw in SUPPORTED_CATEGORIES:
        return raw

    lowered = raw.lower()
    if lowered in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[lowered]

    title = raw.title()
    if title in SUPPORTED_CATEGORIES:
        return title

    return "Others"
