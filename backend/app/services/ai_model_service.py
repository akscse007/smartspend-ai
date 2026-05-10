from pathlib import Path

from app.ml.train_model import train_and_save


def retrain_model(
    dataset: list[dict],
    model_path: str,
    algorithm: str = "logistic_regression",
) -> dict:
    supported = {"logistic_regression", "random_forest", "lstm"}
    if algorithm not in supported:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Supported values: {', '.join(sorted(supported))}.")

    result = train_and_save(Path(model_path), rows=dataset, algorithm=algorithm)
    return {
        "model_path": result["model_path"],
        "algorithm": result["algorithm"],
        "trained_samples": result["trained_samples"],
        "distinct_categories": result["distinct_categories"],
        "text_embedding_backend": result["text_embedding_backend"],
    }
