from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
except ImportError:  # pragma: no cover - runtime optional dependency
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    Dataset = object  # type: ignore[assignment]
    DataLoader = object  # type: ignore[assignment]

NNModuleBase = nn.Module if nn is not None else object  # type: ignore[union-attr]


SEQUENCE_MODEL_DEPENDENCY_MESSAGE = (
    "PyTorch is required for the LSTM model. Install `torch` in the backend environment before using algorithm='lstm'."
)


def ensure_sequence_dependencies() -> None:
    if torch is None or nn is None:
        raise ValueError(SEQUENCE_MODEL_DEPENDENCY_MESSAGE)


def _tokenize(text: str) -> list[str]:
    return [token for token in (text or "").split() if token]


def _pad_sequence(tokens: list[int], max_len: int) -> list[int]:
    trimmed = tokens[:max_len]
    if len(trimmed) < max_len:
        trimmed = trimmed + [0] * (max_len - len(trimmed))
    return trimmed


class SequenceDataset(Dataset):  # type: ignore[misc]
    def __init__(self, sequences: list[list[int]], numerics: list[list[float]], labels: list[int]) -> None:
        ensure_sequence_dependencies()
        self.sequences = torch.tensor(sequences, dtype=torch.long)
        self.numerics = torch.tensor(numerics, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self) -> int:
        return int(self.labels.shape[0])

    def __getitem__(self, idx: int):
        return self.sequences[idx], self.numerics[idx], self.labels[idx]


class ExpenseSequenceNetwork(NNModuleBase):  # type: ignore[misc]
    def __init__(self, vocab_size: int, numeric_size: int, num_classes: int) -> None:
        ensure_sequence_dependencies()
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, 64, padding_idx=0)
        self.encoder = nn.LSTM(
            input_size=64,
            hidden_size=96,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0.0,
        )
        self.numeric_head = nn.Sequential(
            nn.Linear(numeric_size, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
        )
        self.classifier = nn.Sequential(
            nn.Linear(96 * 2 + 32, 96),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(96, num_classes),
        )

    def forward(self, sequences, numerics):
        embedded = self.embedding(sequences)
        outputs, (hidden, _) = self.encoder(embedded)
        del outputs
        sequence_repr = torch.cat((hidden[-2], hidden[-1]), dim=1)
        numeric_repr = self.numeric_head(numerics)
        joined = torch.cat((sequence_repr, numeric_repr), dim=1)
        return self.classifier(joined)


@dataclass
class SequenceArtifacts:
    vocabulary: dict[str, int]
    labels: list[str]
    max_len: int
    numeric_size: int
    state_dict: dict[str, Any]


class SequenceExpenseClassifier:
    def __init__(
        self,
        vocabulary: dict[str, int] | None = None,
        labels: list[str] | None = None,
        max_len: int = 24,
        state_dict: dict[str, Any] | None = None,
    ) -> None:
        self.vocabulary = vocabulary or {"<pad>": 0, "<unk>": 1}
        self.labels = labels or []
        self.max_len = max_len
        self.numeric_size = 5
        self._model = None
        self._device = "cpu"
        if state_dict is not None:
            self._init_model()
            self._model.load_state_dict(state_dict)
            self._model.eval()

    def _combined_text(self, record: dict[str, Any]) -> str:
        return f"{record.get('text', '')} {record.get('merchant', '')} {record.get('merchant_keywords', '')}".strip()

    def _numeric_features(self, record: dict[str, Any]) -> list[float]:
        return [
            float(record.get("abs_amount", 0.0)),
            float(record.get("amount_bucket", 0.0)),
            float(record.get("transaction_frequency", 0.0)),
            float(record.get("historical_category_patterns", 0.0)),
            float(record.get("category_repeat_ratio", 0.0)),
        ]

    def _build_vocab(self, records: list[dict[str, Any]]) -> None:
        counter: Counter[str] = Counter()
        for record in records:
            counter.update(_tokenize(self._combined_text(record)))
        self.vocabulary = {"<pad>": 0, "<unk>": 1}
        for token, count in counter.most_common(6000):
            if count < 1:
                continue
            self.vocabulary[token] = len(self.vocabulary)

    def _encode_record(self, record: dict[str, Any]) -> list[int]:
        tokens = _tokenize(self._combined_text(record))
        encoded = [self.vocabulary.get(token, self.vocabulary["<unk>"]) for token in tokens]
        return _pad_sequence(encoded, self.max_len)

    def _init_model(self) -> None:
        ensure_sequence_dependencies()
        self._device = "cpu"
        self._model = ExpenseSequenceNetwork(
            vocab_size=max(len(self.vocabulary), 2),
            numeric_size=self.numeric_size,
            num_classes=max(len(self.labels), 2),
        ).to(self._device)

    def fit(self, records: list[dict[str, Any]], labels: list[str]) -> "SequenceExpenseClassifier":
        ensure_sequence_dependencies()
        if len(records) < 12:
            raise ValueError("At least 12 labeled rows are required to train the LSTM expense model.")

        self.labels = sorted(set(labels))
        self._build_vocab(records)
        self._init_model()

        label_to_index = {label: idx for idx, label in enumerate(self.labels)}
        sequences = [self._encode_record(record) for record in records]
        numerics = [self._numeric_features(record) for record in records]
        targets = [label_to_index[label] for label in labels]

        dataset = SequenceDataset(sequences, numerics, targets)
        loader = DataLoader(dataset, batch_size=min(16, len(records)), shuffle=True)

        optimizer = torch.optim.Adam(self._model.parameters(), lr=0.003)
        criterion = nn.CrossEntropyLoss()

        self._model.train()
        for _ in range(18):
            for batch_sequences, batch_numerics, batch_labels in loader:
                optimizer.zero_grad()
                logits = self._model(batch_sequences, batch_numerics)
                loss = criterion(logits, batch_labels)
                loss.backward()
                optimizer.step()

        self._model.eval()
        return self

    def predict_with_confidence(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ensure_sequence_dependencies()
        if self._model is None:
            raise RuntimeError("LSTM model has not been trained.")

        sequences = torch.tensor([self._encode_record(record) for record in records], dtype=torch.long)
        numerics = torch.tensor([self._numeric_features(record) for record in records], dtype=torch.float32)

        with torch.no_grad():
            logits = self._model(sequences, numerics)
            probabilities = torch.softmax(logits, dim=1).cpu().numpy()

        predictions: list[dict[str, Any]] = []
        for row in probabilities:
            best_index = max(range(len(row)), key=lambda idx: float(row[idx]))
            predictions.append(
                {
                    "category": self.labels[best_index],
                    "confidence": float(row[best_index]),
                    "model_source": "lstm_sequence",
                }
            )
        return predictions

    def to_bundle(self) -> dict[str, Any]:
        if self._model is None:
            raise RuntimeError("LSTM model has not been trained.")
        return {
            "model_kind": "lstm",
            "vocabulary": self.vocabulary,
            "labels": self.labels,
            "max_len": self.max_len,
            "numeric_size": self.numeric_size,
            "state_dict": self._model.state_dict(),
            "model_source": "lstm_sequence",
        }

    @classmethod
    def from_bundle(cls, bundle: dict[str, Any]) -> "SequenceExpenseClassifier":
        ensure_sequence_dependencies()
        classifier = cls(
            vocabulary=bundle["vocabulary"],
            labels=bundle["labels"],
            max_len=int(bundle.get("max_len", 24)),
            state_dict=bundle["state_dict"],
        )
        classifier.numeric_size = int(bundle.get("numeric_size", 5))
        return classifier


def load_sequence_bundle(path: Path) -> SequenceExpenseClassifier:
    import joblib

    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or bundle.get("model_kind") != "lstm":
        raise ValueError(f"File {path} is not a valid LSTM model bundle.")
    return SequenceExpenseClassifier.from_bundle(bundle)
