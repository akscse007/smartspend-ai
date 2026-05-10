from collections import Counter
from dataclasses import dataclass
from math import log1p

from app.ml.preprocess import ProcessedText, preprocess_description


@dataclass(slots=True)
class FeatureContext:
    merchant_frequency: int = 0
    merchant_top_category_ratio: float = 0.0
    category_repeat_ratio: float = 0.0


@dataclass(slots=True)
class FeatureRecord:
    text: str
    merchant: str
    merchant_keywords: str
    amount: float
    abs_amount: float
    amount_bucket: float
    transaction_frequency: float
    historical_category_patterns: float
    category_repeat_ratio: float


def amount_bucket(amount: float) -> float:
    absolute = abs(amount)
    if absolute == 0:
        return 0.0
    return round(log1p(absolute), 4)


def build_feature_record(
    description: str,
    amount: float = 0.0,
    context: FeatureContext | None = None,
    processed: ProcessedText | None = None,
) -> FeatureRecord:
    processed_text = processed or preprocess_description(description)
    feature_context = context or FeatureContext()
    absolute_amount = abs(float(amount or 0.0))
    return FeatureRecord(
        text=processed_text.cleaned_text,
        merchant=processed_text.merchant,
        merchant_keywords=processed_text.merchant_keywords,
        amount=float(amount or 0.0),
        abs_amount=absolute_amount,
        amount_bucket=amount_bucket(absolute_amount),
        transaction_frequency=float(feature_context.merchant_frequency),
        historical_category_patterns=float(feature_context.merchant_top_category_ratio),
        category_repeat_ratio=float(feature_context.category_repeat_ratio),
    )


def build_context_from_history(history_rows: list[dict], merchant: str, category: str | None = None) -> FeatureContext:
    merchant_rows = [row for row in history_rows if row.get("merchant") == merchant]
    if not merchant_rows:
        return FeatureContext()

    category_counts = Counter(row.get("category") for row in merchant_rows if row.get("category"))
    top_count = max(category_counts.values()) if category_counts else 0
    repeat_count = category_counts.get(category, 0) if category else 0
    total = len(merchant_rows)
    return FeatureContext(
        merchant_frequency=total,
        merchant_top_category_ratio=(top_count / total) if total else 0.0,
        category_repeat_ratio=(repeat_count / total) if total else 0.0,
    )
