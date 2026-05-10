from app.ml.predict import PredictionEngine


class CategorizationService:
    def __init__(self, model_path: str):
        self.engine = PredictionEngine(model_path)

    def reload_model(self) -> None:
        self.engine.reload_model()

    def predict(self, description: str, amount: float = 0.0, history_rows: list[dict] | None = None) -> dict:
        return self.engine.predict(description=description, amount=amount, history_rows=history_rows)

    def predict_many(self, rows: list[dict], history_rows: list[dict] | None = None) -> list[dict]:
        history = history_rows or []
        return [
            self.predict(
                description=str(row.get("description") or ""),
                amount=float(row.get("amount", 0.0) or 0.0),
                history_rows=history,
            )
            for row in rows
        ]
