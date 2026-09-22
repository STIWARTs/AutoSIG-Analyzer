from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.ml.classifier import CLASS_NAMES, ModulationCNN, WINDOW_SIZE  # noqa: E402


def _file_windows(path: Path, rng: np.random.Generator, windows: int = 12) -> np.ndarray:
    x = np.fromfile(path, dtype=np.complex64)
    if len(x) < WINDOW_SIZE:
        x = np.pad(x, (0, WINDOW_SIZE - len(x)))
    starts = rng.integers(0, len(x) - WINDOW_SIZE + 1, size=windows)
    result = []
    for start in starts:
        segment = x[start:start + WINDOW_SIZE]
        segment = segment / (np.sqrt(np.mean(np.abs(segment) ** 2)) + 1e-9)
        result.append(np.stack((segment.real, segment.imag)))
    return np.asarray(result, dtype=np.float32)


def _load_split(dataset_dir: Path, test_fraction: float, seed: int) -> tuple[TensorDataset, TensorDataset]:
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(seed)
    random.Random(seed).shuffle(manifest)
    split = max(2, int(len(manifest) * (1 - test_fraction)))
    train_rows, test_rows = manifest[:split], manifest[split:]
    label_index = {name: index for index, name in enumerate(CLASS_NAMES)}

    def make_dataset(rows):
        xs, ys = [], []
        for row in rows:
            windows = _file_windows(dataset_dir / row["iq"], rng)
            xs.append(windows)
            ys.extend([label_index[row["label"]]] * len(windows))
        return TensorDataset(torch.tensor(np.concatenate(xs)), torch.tensor(ys, dtype=torch.long))
    return make_dataset(train_rows), make_dataset(test_rows)


def train(dataset_dir: Path, model_path: Path, epochs: int = 18, seed: int = 7) -> float:
    torch.manual_seed(seed)
    np.random.seed(seed)
    train_data, test_data = _load_split(dataset_dir, 0.20, seed)
    train_loader = DataLoader(train_data, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_data, batch_size=128)
    model = ModulationCNN(len(CLASS_NAMES))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        for x, y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * len(y)
        print(f"epoch {epoch + 1:02d}/{epochs}: loss={total_loss / len(train_data):.4f}")
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in test_loader:
            prediction = model(x).argmax(dim=1)
            correct += int((prediction == y).sum())
            total += len(y)
    accuracy = correct / total
    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state": model.state_dict(), "classes": CLASS_NAMES, "window_size": WINDOW_SIZE,
                "held_out_accuracy": accuracy, "training_files": len(train_data), "test_windows": total}, model_path)
    (model_path.with_suffix(".metrics.json")).write_text(json.dumps({"held_out_window_accuracy": accuracy,
                                                                        "test_windows": total}, indent=2))
    print(f"Held-out accuracy: {accuracy:.2%} ({total} windows)")
    return accuracy


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the AutoSIG raw I/Q CNN")
    parser.add_argument("--dataset", type=Path, default=ROOT / "datasets")
    parser.add_argument("--model", type=Path, default=ROOT / "models" / "modulation_cnn.pt")
    parser.add_argument("--epochs", type=int, default=18)
    args = parser.parse_args()
    train(args.dataset, args.model, args.epochs)
