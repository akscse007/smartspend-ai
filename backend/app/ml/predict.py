from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib

from app.ml.feature_engineering import build_context_from_history, build_feature_record
from app.ml.merchant_rules import match_merchant_rule, merchant_logo_url
from app.ml.preprocess import preprocess_description
from app.ml.sequence_model import SequenceExpenseClassifier


UNCERTAIN_THRESHOLD = 0.6


class PredictionEngine:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self.model: Any | None = None
        self.reload_model()

    def reload_model(self) -> None:
        path = Path(self.model_path)
        if not path.exists():
            self.model = None
            return

        loaded = joblib.load(path)
        if isinstance(loaded, dict) and loaded.get("model_kind") == "lstm":
            self.model = SequenceExpenseClassifier.from_bundle(loaded)
            return
        self.model = loaded

    def predict(
        self,
        description: str,
        amount: float = 0.0,
        history_rows: list[dict] | None = None,
    ) -> dict:
        rule_match = match_merchant_rule(description)
        processed = preprocess_description(description)

        if rule_match is not None:
            return {
                "description": description,
                "merchant": rule_match["merchant"],
                "predicted_category": rule_match["category"],
                "confidence": round(rule_match["confidence"], 4),
                "model_source": rule_match["source"],
                "merchant_logo": merchant_logo_url(rule_match.get("domain")),
                "features": {},
            }

        context = build_context_from_history(history_rows or [], processed.merchant)
        features = build_feature_record(description=description, amount=amount, context=context, processed=processed)
        if self.model is None:
            return {
                "description": description,
                "merchant": processed.merchant,
                "predicted_category": "Uncertain",
                "confidence": 0.0,
                "model_source": "unavailable",
                "merchant_logo": None,
                "features": asdict(features),
            }

        prediction = self.model.predict_with_confidence([asdict(features)])[0]
        category = prediction["category"]
        confidence = float(prediction["confidence"])
        if confidence < UNCERTAIN_THRESHOLD:
            category = "Uncertain"

        return {
            "description": description,
            "merchant": processed.merchant,
            "predicted_category": category,
            "confidence": round(confidence, 4),
            "model_source": prediction.get("model_source", "ml"),
            "merchant_logo": None,
            "features": asdict(features),
        }
