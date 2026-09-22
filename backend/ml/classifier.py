from __future__ import annotations

from pathlib import Path
import numpy as np
import torch
from torch import nn

CLASS_NAMES = ("BPSK", "QPSK")
WINDOW_SIZE = 256


class ModulationCNN(nn.Module):
    def __init__(self, classes: int = 2) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(2, 32, 7, padding=3), nn.BatchNorm1d(32), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 5, padding=2), nn.BatchNorm1d(64), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(64, 96, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool1d(16),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(96 * 16, 128), nn.ReLU(), nn.Dropout(0.2),
                                        nn.Linear(128, classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x))


def load_classifier(model_path: str | Path | None = None) -> tuple[ModulationCNN, dict]:
    path = Path(model_path or Path(__file__).resolve().parents[2] / "models" / "modulation_cnn.pt")
    if not path.exists():
        raise FileNotFoundError(f"Trained classifier not found at {path}. Run training/train_classifier.py first.")
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    model = ModulationCNN(len(checkpoint.get("classes", CLASS_NAMES)))
    model.load_state_dict(checkpoint["model_state"])
    model.eval()
    return model, checkpoint


def _windows(samples: np.ndarray, window_size: int) -> np.ndarray:
    x = np.asarray(samples, dtype=np.complex64)
    if len(x) < window_size:
        x = np.pad(x, (0, window_size - len(x)))
    count = min(32, max(1, len(x) // window_size))
    starts = np.linspace(0, max(0, len(x) - window_size), count, dtype=int)
    result = []
    for start in starts:
        window = x[start:start + window_size]
        window = window / (np.sqrt(np.mean(np.abs(window) ** 2)) + 1e-9)
        result.append(np.stack((window.real, window.imag)))
    return np.asarray(result, dtype=np.float32)


def classify_samples(samples: np.ndarray, model_path: str | Path | None = None) -> dict[str, float]:
    model, checkpoint = load_classifier(model_path)
    classes = tuple(checkpoint.get("classes", CLASS_NAMES))
    window_size = int(checkpoint.get("window_size", WINDOW_SIZE))
    with torch.no_grad():
        logits = model(torch.from_numpy(_windows(samples, window_size)))
        probabilities = torch.softmax(logits, dim=1).mean(dim=0).numpy()
    return {name: float(probabilities[index]) for index, name in enumerate(classes)}
