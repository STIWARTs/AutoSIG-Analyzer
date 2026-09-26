from __future__ import annotations

import argparse
import json
import sys
import importlib.util
from pathlib import Path

import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.recovery.coding import block_interleave, convolutional_encode, make_frame  # noqa: E402
_flowgraph_spec = importlib.util.spec_from_file_location("autosig_synthetic_flowgraph", ROOT / "gnuradio" / "synthetic_flowgraph.py")
assert _flowgraph_spec and _flowgraph_spec.loader
_flowgraph = importlib.util.module_from_spec(_flowgraph_spec)
_flowgraph_spec.loader.exec_module(_flowgraph)
run_flowgraph = _flowgraph.run_flowgraph

SAMPLE_RATE = 48_000
SAMPLES_PER_SYMBOL = 8


def qpsk_map(bits: np.ndarray) -> np.ndarray:
    paired = np.asarray(bits, dtype=np.int8).reshape(-1, 2)
    real = 1 - 2 * paired[:, 0]
    imag = 1 - 2 * (paired[:, 0] ^ paired[:, 1])
    return ((real + 1j * imag) / np.sqrt(2)).astype(np.complex64)


def bpsk_map(bits: np.ndarray) -> np.ndarray:
    return (1 - 2 * np.asarray(bits, dtype=np.int8)).astype(np.float32).astype(np.complex64)


def _write_sigmf(path: Path, snr_db: float, offset_hz: float, modulation: str, generator: str) -> None:
    metadata = {
        "global": {"core:datatype": "cf32_le", "core:sample_rate": SAMPLE_RATE,
                   "core:description": f"{generator} generated {modulation}; SNR {snr_db:.1f} dB"},
        "captures": [{"core:sample_start": 0, "core:frequency": 0.0}],
        "annotations": [{"core:label": modulation, "autosig:snr_db": snr_db,
                         "autosig:frequency_offset_hz": offset_hz,
                         "autosig:interleaving": "Block", "autosig:fec": "Convolutional/Viterbi"}],
    }
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _write_wav(complex_samples: np.ndarray, path: Path) -> None:
    stereo = np.column_stack((complex_samples.real, complex_samples.imag))
    wavfile.write(path, SAMPLE_RATE, np.clip(stereo * 32767, -32768, 32767).astype(np.int16))


def generate(output: Path, count_per_class: int = 32, seed: int = 20260922) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    manifest = []
    snrs = (-2.0, 0.0, 4.0, 8.0, 12.0, 18.0)
    for modulation in ("QPSK", "BPSK"):
        for index in range(count_per_class):
            payload = rng.integers(0, 2, 128, dtype=np.uint8)
            frame = make_frame(payload)
            encoded = convolutional_encode(frame, terminate=True)
            interleaved = block_interleave(encoded)
            symbols = qpsk_map(interleaved) if modulation == "QPSK" else bpsk_map(interleaved)
            snr_db = float(snrs[index % len(snrs)])
            offset_hz = float(rng.uniform(-85.0, 85.0))
            stem = f"{modulation.lower()}_{index:03d}_snr{snr_db:+.0f}_cfo{offset_hz:+.0f}"
            iq_path = output / f"{stem}.iq"
            generator = run_flowgraph(symbols, iq_path, SAMPLE_RATE, SAMPLES_PER_SYMBOL, offset_hz, snr_db)
            values = np.fromfile(iq_path, dtype=np.complex64)
            _write_sigmf(output / f"{stem}.sigmf-meta", snr_db, offset_hz, modulation, generator)
            _write_wav(values, output / f"{stem}.wav")
            manifest.append({"iq": iq_path.name, "wav": f"{stem}.wav", "label": modulation,
                             "snr_db": snr_db, "frequency_offset_hz": offset_hz,
                             "generator": generator, "sample_rate": SAMPLE_RATE})
            print(f"Generated {iq_path.name}")
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate labeled QPSK/BPSK AutoSIG captures "
                                                  "(GNU Radio flowgraph when available, else the explicitly "
                                                  "labeled NumPy flowgraph-equivalent fallback)")
    parser.add_argument("--output", type=Path, default=ROOT / "datasets")
    parser.add_argument("--count-per-class", type=int, default=32)
    args = parser.parse_args()
    print(f"Manifest: {generate(args.output, args.count_per_class)}")
