from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

import joblib

from app.ml.categories import SUPPORTED_CATEGORIES, normalize_category_label
from app.ml.feature_engineering import build_context_from_history, build_feature_record
from app.ml.sequence_model import SequenceExpenseClassifier


SEED_TRAINING_ROWS = [
    {"description": "Zomato dinner order", "amount": 420, "merchant": "zomato", "category": "Food"},
    {"description": "Swiggy lunch combo", "amount": 285, "merchant": "swiggy", "category": "Food"},
    {"description": "Cafe coffee day bill", "amount": 195, "merchant": "cafe", "category": "Food"},
    {"description": "Uber ride to office", "amount": 340, "merchant": "uber", "category": "Transport"},
    {"description": "Ola cab airport drop", "amount": 560, "merchant": "ola", "category": "Transport"},
    {"description": "Metro card recharge", "amount": 200, "merchant": "metro", "category": "Transport"},
    {"description": "Bigbasket weekly groceries", "amount": 1480, "merchant": "bigbasket", "category": "Groceries"},
    {"description": "Blinkit vegetables order", "amount": 640, "merchant": "blinkit", "category": "Groceries"},
    {"description": "Supermarket grocery basket", "amount": 1890, "merchant": "supermarket", "category": "Groceries"},
    {"description": "Amazon shopping order", "amount": 1299, "merchant": "amazon", "category": "Shopping"},
    {"description": "Flipkart fashion purchase", "amount": 2299, "merchant": "flipkart", "category": "Shopping"},
    {"description": "Myntra shoes purchase", "amount": 3199, "merchant": "myntra", "category": "Shopping"},
    {"description": "Electricity bill payment", "amount": 2450, "merchant": "electricity", "category": "Bills"},
    {"description": "Jio fiber internet bill", "amount": 999, "merchant": "jio", "category": "Bills"},
    {"description": "Water bill payment", "amount": 720, "merchant": "water bill", "category": "Bills"},
    {"description": "Apollo pharmacy medicine", "amount": 875, "merchant": "apollo pharmacy", "category": "Healthcare"},
    {"description": "Doctor consultation fee", "amount": 1200, "merchant": "doctor", "category": "Healthcare"},
    {"description": "Clinic lab test", "amount": 1650, "merchant": "clinic", "category": "Healthcare"},
    {"description": "Bookmyshow movie tickets", "amount": 980, "merchant": "bookmyshow", "category": "Entertainment"},
    {"description": "Inox cinema snacks", "amount": 430, "merchant": "inox", "category": "Entertainment"},
    {"description": "Gaming subscription top up", "amount": 799, "merchant": "gaming", "category": "Entertainment"},
    {"description": "IRCTC train booking", "amount": 2250, "merchant": "irctc", "category": "Travel"},
    {"description": "Air India flight booking", "amount": 6840, "merchant": "air india", "category": "Travel"},
    {"description": "Hotel stay booking", "amount": 4550, "merchant": "hotel", "category": "Travel"},
    {"description": "Netflix monthly plan", "amount": 649, "merchant": "netflix", "category": "Subscriptions"},
    {"description": "Spotify premium membership", "amount": 119, "merchant": "spotify", "category": "Subscriptions"},
    {"description": "Amazon Prime annual membership", "amount": 1499, "merchant": "amazon prime", "category": "Subscriptions"},
    {"description": "ATM withdrawal cash", "amount": 1000, "merchant": "atm", "category": "Others"},
    {"description": "Gift purchase for friend", "amount": 850, "merchant": "gift", "category": "Others"},
    {"description": "Miscellaneous household payment", "amount": 610, "merchant": "misc", "category": "Others"},
]


class SimpleBayesTextClassifier:
    def __init__(self) -> None:
        self.classes_: list[str] = []
        self._priors: dict[str, float] = {}
        self._token_counts: dict[str, Counter[str]] = {}
        self._merchant_counts: dict[str, Counter[str]] = {}
        self._amount_buckets: dict[str, float] = {}

    def fit(self, records: list[dict[str, Any]], labels: list[str]) -> "SimpleBayesTextClassifier":
        class_counts = Counter(labels)
        token_counts = {label: Counter() for label in class_counts}
        merchant_counts = {label: Counter() for label in class_counts}
        amount_totals = {label: 0.0 for label in class_counts}
        for record, label in zip(records, labels):
            tokens = f"{record['text']} {record['merchant']} {record['merchant_keywords']}".split()
            for token in tokens:
                token_counts[label][token] += 1
            merchant_counts[label][record["merchant"]] += 1
            amount_totals[label] += float(record.get("amount_bucket", 0.0))

        total_docs = sum(class_counts.values()) or 1
        self.classes_ = sorted(class_counts.keys())
        self._priors = {label: count / total_docs for label, count in class_counts.items()}
        self._token_counts = token_counts
        self._merchant_counts = merchant_counts
        self._amount_buckets = {
            label: (amount_totals[label] / class_counts[label]) if class_counts[label] else 0.0
            for label in class_counts
        }
        return self

    def predict_with_confidence(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        predictions: list[dict[str, Any]] = []
        for record in records:
            tokens = f"{record['text']} {record['merchant']} {record['merchant_keywords']}".split()
            merchant = record["merchant"]
            amount_bucket = float(record.get("amount_bucket", 0.0))
            scores: dict[str, float] = {}
            evidence_found = False
            for label in self.classes_:
                token_counter = self._token_counts[label]
                token_total = sum(token_counter.values()) or 1
                token_score = sum(token_counter.get(token, 0) for token in tokens) / token_total if tokens else 0.0

                merchant_counter = self._merchant_counts[label]
                merchant_total = sum(merchant_counter.values()) or 1
                merchant_score = merchant_counter.get(merchant, 0) / merchant_total
                evidence_found = evidence_found or token_score > 0 or merchant_score > 0

                bucket_center = self._amount_buckets.get(label, 0.0)
                amount_score = max(0.0, 1 - (abs(amount_bucket - bucket_center) / max(bucket_center, 1.0)))
                prior_score = self._priors.get(label, 0.0)

                scores[label] = (token_score * 0.55) + (merchant_score * 0.2) + (amount_score * 0.15) + (prior_score * 0.1)

            if not evidence_found or max(scores.values(), default=0.0) <= 0:
                predictions.append(
                    {
                        "category": "Others",
                        "confidence": 0.55,
                        "model_source": "naive_bayes_fallback",
                    }
                )
                continue

            total = sum(scores.values()) or 1.0
            label, raw_score = max(scores.items(), key=lambda item: item[1])
            predictions.append(
                {
                    "category": label,
                    "confidence": raw_score / total,
                    "model_source": "naive_bayes_fallback",
                }
            )
        return predictions


class HybridExpenseClassifier:
    def __init__(self, algorithm: str = "logistic_regression", text_embedding_backend: str = "tfidf") -> None:
        self.algorithm = algorithm
        self.text_embedding_backend = text_embedding_backend
        self.text_vectorizer: Any | None = None
        self.merchant_vectorizer: Any | None = None
        self.numeric_scaler: Any | None = None
        self.classifier: Any | None = None
        self.classes_: list[str] = []

    def _numeric_matrix(self, records: list[dict[str, Any]], fit: bool = False):
        import numpy as np
        from scipy import sparse
        from sklearn.preprocessing import StandardScaler

        matrix = np.array(
            [
                [
                    float(record.get("abs_amount", 0.0)),
                    float(record.get("amount_bucket", 0.0)),
                    float(record.get("transaction_frequency", 0.0)),
                    float(record.get("historical_category_patterns", 0.0)),
                    float(record.get("category_repeat_ratio", 0.0)),
                ]
                for record in records
            ],
            dtype=float,
        )
        if fit or self.numeric_scaler is None:
            self.numeric_scaler = StandardScaler()
            matrix = self.numeric_scaler.fit_transform(matrix)
        else:
            matrix = self.numeric_scaler.transform(matrix)
        return sparse.csr_matrix(matrix)

    def _text_matrix(self, records: list[dict[str, Any]], fit: bool = False):
        from scipy import sparse
        from sklearn.feature_extraction.text import TfidfVectorizer

        combined_text = [f"{row['text']} {row['merchant']} {row['merchant_keywords']}".strip() for row in records]
        merchant_text = [row["merchant"] for row in records]

        if fit or self.text_vectorizer is None:
            self.text_vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=8000, sublinear_tf=True)
            self.merchant_vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
            text_matrix = self.text_vectorizer.fit_transform(combined_text)
            merchant_matrix = self.merchant_vectorizer.fit_transform(merchant_text)
        else:
            text_matrix = self.text_vectorizer.transform(combined_text)
            merchant_matrix = self.merchant_vectorizer.transform(merchant_text)

        numeric_matrix = self._numeric_matrix(records, fit=fit)
        return sparse.hstack([text_matrix, merchant_matrix, numeric_matrix], format="csr")

    def fit(self, records: list[dict[str, Any]], labels: list[str]) -> "HybridExpenseClassifier":
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression

        features = self._text_matrix(records, fit=True)
        if self.algorithm == "random_forest":
            self.classifier = RandomForestClassifier(
                n_estimators=240,
                max_depth=18,
                min_samples_leaf=1,
                class_weight="balanced_subsample",
                random_state=42,
            )
        else:
            self.algorithm = "logistic_regression"
            self.classifier = LogisticRegression(max_iter=2200, class_weight="balanced")

        self.classifier.fit(features, labels)
        self.classes_ = [str(label) for label in getattr(self.classifier, "classes_", sorted(set(labels)))]
        return self

    def predict_with_confidence(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.classifier is None:
            raise RuntimeError("Model has not been trained.")

        features = self._text_matrix(records, fit=False)
        probabilities = self.classifier.predict_proba(features)
        predictions: list[dict[str, Any]] = []
        for row in probabilities:
            best_index = max(range(len(row)), key=lambda idx: float(row[idx]))
            predictions.append(
                {
                    "category": self.classes_[best_index],
                    "confidence": float(row[best_index]),
                    "model_source": self.text_embedding_backend,
                }
            )
        return predictions


MODULE_ALIAS = "app.ml.train_model"
sys.modules.setdefault(MODULE_ALIAS, sys.modules[__name__])
SimpleBayesTextClassifier.__module__ = MODULE_ALIAS
HybridExpenseClassifier.__module__ = MODULE_ALIAS


def _build_training_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    cleaned_rows: list[dict[str, Any]] = []
    labels: list[str] = []
    history_rows: list[dict[str, Any]] = []

    for row in rows:
        description = str(row.get("description") or row.get("clean_description") or "").strip()
        category = normalize_category_label(row.get("category"))
        if not description or category not in SUPPORTED_CATEGORIES:
            continue

        merchant = str(row.get("merchant") or "").strip()
        history_context = build_context_from_history(history_rows, merchant=merchant or "unknown", category=category)
        feature = build_feature_record(
            description=description,
            amount=float(row.get("amount_inr", row.get("amount", 0.0)) or 0.0),
            context=history_context,
        )
        cleaned_rows.append(asdict(feature))
        labels.append(category)
        history_rows.append({"merchant": feature.merchant, "category": category})

    return cleaned_rows, labels


def training_rows() -> list[dict[str, Any]]:
    return list(SEED_TRAINING_ROWS)


def train_expense_model(
    rows: list[dict[str, Any]] | None = None,
    algorithm: str = "logistic_regression",
) -> tuple[Any, dict[str, Any]]:
    rows = rows or training_rows()
    features, labels = _build_training_rows(rows)
    if len(features) < 12:
        raise ValueError("At least 12 labeled rows are required to train the expense model.")

    category_counts = Counter(labels)
    if len(category_counts) < 2:
        raise ValueError("At least two distinct categories are required to train the expense model.")

    try:
        if algorithm == "lstm":
            model = SequenceExpenseClassifier().fit(features, labels)
            backend = "lstm_sequence"
        else:
            model = HybridExpenseClassifier(algorithm=algorithm).fit(features, labels)
            backend = model.text_embedding_backend
    except ValueError:
        raise
    except Exception:
        model = SimpleBayesTextClassifier().fit(features, labels)
        backend = "naive_bayes_fallback"
        algorithm = "naive_bayes_fallback"

    metadata = {
        "algorithm": algorithm,
        "text_embedding_backend": backend,
        "trained_samples": len(features),
        "distinct_categories": len(category_counts),
        "categories": sorted(category_counts.keys()),
    }
    return model, metadata


def train_and_save(out_path: Path, rows: list[dict[str, Any]] | None = None, algorithm: str = "logistic_regression") -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model, metadata = train_expense_model(rows=rows, algorithm=algorithm)
    if isinstance(model, SequenceExpenseClassifier):
        joblib.dump(model.to_bundle(), out_path)
    else:
        joblib.dump(model, out_path)
    metadata["model_path"] = str(out_path)
    return metadata


if __name__ == "__main__":
    target = Path(__file__).parent / "ml_model.pkl"
    result = train_and_save(target)
    print(f"Saved model to {result['model_path']} with {result['trained_samples']} samples")
