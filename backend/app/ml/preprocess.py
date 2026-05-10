import re
from dataclasses import dataclass


STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "payment",
    "paytm",
    "purchase",
    "spent",
    "the",
    "to",
    "txn",
    "upi",
    "via",
    "wallet",
    "with",
    "xx",
    "xxxx",
}

MERCHANT_NORMALIZATION = {
    "amazonpay": "amazon",
    "amazon prime": "amazon prime",
    "amazon": "amazon",
    "apollo pharmacy": "apollo pharmacy",
    "bigbasket": "bigbasket",
    "bookmyshow": "bookmyshow",
    "flipkart": "flipkart",
    "irctc": "irctc",
    "jio": "jio",
    "netflix": "netflix",
    "ola": "ola",
    "spicejet": "spicejet",
    "spotify": "spotify",
    "swiggy": "swiggy",
    "uber": "uber",
    "zomato": "zomato",
}


@dataclass(slots=True)
class ProcessedText:
    raw_text: str
    cleaned_text: str
    merchant: str
    merchant_keywords: str
    tokens: list[str]


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_transaction_description(text: str) -> str:
    lowered = (text or "").lower().strip()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return _normalize_spaces(lowered)


def remove_stopwords(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token and token not in STOPWORDS and not token.isdigit()]


def normalize_merchant_name(cleaned_text: str) -> str:
    for alias, canonical in MERCHANT_NORMALIZATION.items():
        if alias in cleaned_text:
            return canonical

    tokens = [token for token in cleaned_text.split() if len(token) > 2]
    return " ".join(tokens[:2]) if tokens else "unknown"


def preprocess_description(text: str) -> ProcessedText:
    cleaned = clean_transaction_description(text)
    merchant = normalize_merchant_name(cleaned)
    stripped = cleaned.replace(merchant, " ").strip() if merchant != "unknown" else cleaned
    tokens = remove_stopwords(_normalize_spaces(stripped).split())
    merchant_keywords = " ".join(tokens[:4]) if tokens else merchant
    cleaned_text = _normalize_spaces(" ".join(tokens)) or merchant
    return ProcessedText(
        raw_text=text or "",
        cleaned_text=cleaned_text,
        merchant=merchant,
        merchant_keywords=merchant_keywords,
        tokens=tokens,
    )
