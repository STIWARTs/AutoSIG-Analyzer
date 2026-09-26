"""Deterministic reconstruction of the synthetic corpus ground truth.

Step 3 evaluation-only. Nothing in the production pipeline imports this module.

The shipped corpus was produced by ``training.generate_dataset.generate()``
using the NumPy fallback in ``gnuradio/synthetic_flowgraph.py``. That generator
draws every capture from a single seeded RNG in a fixed order, so the true
payload/frame bits can be reconstructed exactly -- *provided* the reproduction
is anchored to the on-disk bytes. The anchoring is the integrity gate:

    reproduce_iq_samples(truth...) is written through the very same
    run_flowgraph(), read back, and required to be bit-identical
    (np.array_equal) to the file under evaluation.

If the seed, loop order, draw sequence, coding constants, or the file itself
ever diverge, the gate fails and that capture is excluded from scoring rather
than measured against a possibly-wrong payload. This module deliberately
reuses the generator's own symbols/flowgraph/coding functions instead of
re-implementing them, so there is a single source of truth for every value it
can reuse. The two facts that are *not* exposed as importable constants by
generate() -- the SNR cycling tuple and the modulation loop order -- are
mirrored below and are validated by the integrity gate on every capture.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import numpy as np

from backend.recovery.coding import (PREAMBLE, HEADER, block_interleave,
                                     convolutional_encode, make_frame)
# Reuse the generator's own symbol mappers, flowgraph, and structural constants
# rather than re-deriving them. Importing training.generate_dataset is safe:
# its argparse entry point is guarded by ``if __name__ == "__main__"``.
from training.generate_dataset import (SAMPLE_RATE, SAMPLES_PER_SYMBOL, bpsk_map,
                                       qpsk_map, run_flowgraph)

# --- Mirrored from generate_dataset.generate(); validated per-capture by the IQ-identity gate.
SEED = 20260922
COUNT_PER_CLASS = 32
MODULATION_ORDER = ("QPSK", "BPSK")
SNR_CYCLE = (-2.0, 0.0, 4.0, 8.0, 12.0, 18.0)

PAYLOAD_BITS = 128
SYNC_BITS = len(PREAMBLE) + len(HEADER)          # 64 fixed PREAMBLE+HEADER bits
FRAME_BITS = SYNC_BITS + PAYLOAD_BITS            # 192


@dataclass(frozen=True)
class CaptureTruth:
    """All ground truth reconstructable for one corpus capture."""
    key: str                     # stable "qpsk_000" style id (modulation + index)
    modulation: str
    index: int
    snr_db: float
    frequency_offset_hz: float
    payload: np.ndarray          # 128 bits
    frame: np.ndarray            # 192 bits = PREAMBLE + HEADER + payload
    encoded: np.ndarray          # convolutional_encode(frame, terminate=True)
    interleaved: np.ndarray      # block_interleave(encoded) == transmitted bits
    symbols: np.ndarray          # mapped constellation symbols

    @property
    def true_payload(self) -> np.ndarray:
        return self.payload


def capture_key(modulation: str, index: int) -> str:
    return f"{modulation.lower()}_{index:03d}"


def key_from_filename(name: str) -> str:
    """Extract the stable key from any corpus filename.

    Uses only the first two underscore tokens (``modulation_###``); the SNR and
    CFO tokens are rounded in the filename and therefore unsafe to match on.
    """
    stem = Path(name).stem
    parts = stem.split("_")
    if len(parts) < 2:
        raise ValueError(f"Unrecognized corpus filename: {name!r}")
    return f"{parts[0]}_{parts[1]}"


def iter_corpus_truth(seed: int = SEED, count_per_class: int = COUNT_PER_CLASS) -> Iterator[CaptureTruth]:
    """Replay generate_dataset.generate()'s exact RNG consumption order.

    Per capture the generator draws, in this order: payload (rng.integers(128))
    then frequency offset (rng.uniform). SNR is cycled deterministically and
    consumes no RNG. run_flowgraph() uses its own fixed internal noise seeds,
    so it never touches this stream.
    """
    rng = np.random.default_rng(seed)
    for modulation in MODULATION_ORDER:
        for index in range(count_per_class):
            payload = rng.integers(0, 2, PAYLOAD_BITS, dtype=np.uint8)
            frame = make_frame(payload)
            encoded = convolutional_encode(frame, terminate=True)
            interleaved = block_interleave(encoded)
            symbols = qpsk_map(interleaved) if modulation == "QPSK" else bpsk_map(interleaved)
            snr_db = float(SNR_CYCLE[index % len(SNR_CYCLE)])
            offset_hz = float(rng.uniform(-85.0, 85.0))
            yield CaptureTruth(
                key=capture_key(modulation, index), modulation=modulation, index=index,
                snr_db=snr_db, frequency_offset_hz=offset_hz,
                payload=payload, frame=frame, encoded=encoded, interleaved=interleaved, symbols=symbols,
            )


def build_corpus_truth(seed: int = SEED, count_per_class: int = COUNT_PER_CLASS) -> dict[str, CaptureTruth]:
    return {t.key: t for t in iter_corpus_truth(seed=seed, count_per_class=count_per_class)}


def reproduce_iq_samples(symbols: np.ndarray, sample_rate: float, samples_per_symbol: int,
                         frequency_offset_hz: float, snr_db: float) -> np.ndarray:
    """Re-run the generator's flowgraph into a temp file and read the bytes back.

    Uses the real run_flowgraph(), so the reproduction is exactly what the
    committed generator would emit for these symbols/impairments (or, if GNU
    Radio were present, whatever it emits -- which would then fail identity
    against the NumPy-fallback corpus and be reported, not hidden).
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "repro.iq"
        run_flowgraph(symbols, path, sample_rate, samples_per_symbol, frequency_offset_hz, snr_db)
        return np.fromfile(path, dtype=np.complex64)


def verify_iq_identity(truth: CaptureTruth, on_disk_iq_path: Path | str) -> dict:
    """Integrity gate: reproduced waveform must be bit-identical to the file.

    Returns a dict record; ``ok`` is True only when the reproduced IQ equals
    the on-disk IQ element-for-element. Never raises for a mismatch -- the
    caller must treat ok=False as GROUND_TRUTH_MISMATCH and skip BER.
    """
    reproduced = reproduce_iq_samples(truth.symbols, SAMPLE_RATE, SAMPLES_PER_SYMBOL,
                                      truth.frequency_offset_hz, truth.snr_db)
    on_disk = np.fromfile(str(on_disk_iq_path), dtype=np.complex64)
    same_length = len(reproduced) == len(on_disk)
    identical = bool(same_length and np.array_equal(reproduced, on_disk))
    max_diff = (float(np.max(np.abs(reproduced.astype(np.complex128) - on_disk.astype(np.complex128))))
                if same_length and len(on_disk) else None)
    return {
        "ok": identical,
        "reproduced_len": int(len(reproduced)),
        "on_disk_len": int(len(on_disk)),
        "length_match": bool(same_length),
        "max_abs_diff": max_diff,
        "reproduced_frequency_offset_hz": truth.frequency_offset_hz,
    }
