import json
from functools import lru_cache
from pathlib import Path

from app.ml.categories import normalize_category_label
from app.ml.preprocess import preprocess_description


RULES_PATH = Path(__file__).with_name("merchant_rules.json")


@lru_cache(maxsize=1)
def load_merchant_rules() -> list[dict]:
    if not RULES_PATH.exists():
        return []
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def match_merchant_rule(description: str) -> dict | None:
    processed = preprocess_description(description)
    haystack = f"{processed.cleaned_text} {processed.merchant}".strip()

    for rule in load_merchant_rules():
        needle = str(rule.get("match", "")).strip().lower()
        if needle and needle in haystack:
            return {
                "category": normalize_category_label(rule.get("category")),
                "confidence": float(rule.get("confidence", 0.95)),
                "merchant": rule.get("merchant") or processed.merchant,
                "domain": rule.get("domain"),
                "source": "rule",
            }
    return None


def merchant_logo_url(domain: str | None) -> str | None:
    if not domain:
        return None
    return f"https://logo.clearbit.com/{domain}"


def logo_for_merchant(merchant: str | None) -> str | None:
    merchant_name = (merchant or "").strip().lower()
    if not merchant_name:
        return None

    for rule in load_merchant_rules():
        if str(rule.get("merchant", "")).strip().lower() == merchant_name:
            return merchant_logo_url(rule.get("domain"))
    return None
