from __future__ import annotations

import numpy as np


def synchronize_psk(samples: np.ndarray, samples_per_symbol: int, modulation: str) -> tuple[np.ndarray, dict[str, float]]:
    """Blind PSK carrier correction plus maximum constellation-concentration timing phase."""
    order = 4 if modulation == "QPSK" else 2
    x = np.asarray(samples, dtype=np.complex64)
    if len(x) < samples_per_symbol * 16:
        raise ValueError("Recording is too short for synchronization")
    powered = x ** order
    phase = np.unwrap(np.angle(powered))
    slope = np.polyfit(np.arange(len(phase)), phase, 1)[0]
    cfo_rad_per_sample = slope / order
    corrected = x * np.exp(-1j * cfo_rad_per_sample * np.arange(len(x)))
    best_offset, best_metric = 0, -np.inf
    for offset in range(samples_per_symbol):
        symbols = corrected[offset::samples_per_symbol]
        metric = abs(np.mean(symbols ** order)) / (np.mean(np.abs(symbols) ** order) + 1e-12)
        if metric > best_metric:
            best_offset, best_metric = offset, float(metric)
    return corrected[best_offset::samples_per_symbol], {
        "cfo_rad_per_sample": float(cfo_rad_per_sample), "timing_offset": float(best_offset),
        "timing_metric": float(best_metric),
    }
