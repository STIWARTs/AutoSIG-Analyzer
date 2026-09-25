"""Shared, quality-gated carrier-offset estimator.

Single source of truth for CFO estimation, used by both the DSP display path
(backend.dsp.analysis) and the recovery synchronization path (backend.dsp.sync).
The function refuses to guess: it returns None when the spectral peak is too
weak to distinguish from the noise floor, and callers must preserve that None
("no reliable estimate") rather than coercing it to a numeric 0 Hz.
"""
from __future__ import annotations

import numpy as np


def estimate_carrier_offset(x: np.ndarray, fs: float | None, modulation: str | None = None) -> float | None:
    # Measure the carrier rotation instead of trusting metadata: synthetic baseband
    # captures store core:frequency 0.0 (and WAV none at all), which rendered the
    # dashboard as "0.0 / UNAVAILABLE". Squaring is noise-optimal for BPSK (x^2 is
    # a pure tone); the fourth power also strips QPSK modulation. With no
    # classifier hint, evaluate both zero-padded periodograms and keep the peak
    # with the strongest spectral concentration. A peak less than ~4x the band
    # mean is indistinguishable from the noise floor (validated on the labeled
    # corpus), so the measurement is refused rather than reported as a lie.
    if fs is None or len(x) < 128:
        return None
    if modulation == "BPSK":
        orders: tuple[int, ...] = (2,)
    elif modulation == "QPSK":
        orders = (4,)
    else:
        orders = (2, 4)
    best: tuple[float, float] | None = None
    for order in orders:
        n = 8 * len(x)
        powered = x ** order
        powered = powered - powered.mean()  # kill the noise-self-mixing DC lump
        spec = np.abs(np.fft.fft(powered, n))
        freqs = np.fft.fftfreq(n, 1 / fs)
        band = np.abs(freqs) < fs / 8
        indices = np.flatnonzero(band)
        k = int(indices[np.argmax(spec[indices])])
        score = float(spec[k] / (np.mean(spec[band]) + 1e-12))
        if 1 <= k < n - 1:
            a, b, c = spec[k - 1], spec[k], spec[k + 1]
            denom = a - 2 * b + c
            delta = 0.5 * (a - c) / denom if denom != 0 else 0.0
            peak_hz = freqs[k] + delta * (freqs[1] - freqs[0])
        else:
            peak_hz = freqs[k]
        if best is None or score > best[1]:
            best = (float(peak_hz / order), score)
    if best is None or best[1] < 4.0:
        return None
    return best[0]
