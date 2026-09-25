from __future__ import annotations

from typing import Any

import numpy as np

from backend.dsp.carrier import estimate_carrier_offset

# A/B escape hatch for the CFO-estimator refactor: set True to restore the old
# in-file unwrap+polyfit estimator (kept until the corpus before/after results
# are signed off). The legacy path is ungated and was shown on the full corpus
# to drift tens-to-hundreds of Hz off truth below 18 dB SNR, so it must not
# become the default again.
USE_LEGACY_POLYFIT_CFO = False

# Whether to *apply* the carried-forward constant-phase (polyfit intercept) term
# to the recovered signal. The measurement is always computed and preserved in
# info["phase_correction_rad"]; this flag only controls applying it to samples.
# Default False: the fourth-power phase is quadrant-ambiguous and applying it raw
# lands near the +/-45-degree QPSK decision boundary, corrupting demodulation on
# the corpus (IQ Frame-Validation pass 42/64 -> 28/64 when applied). The Recovery
# Chain's own discrete {0,90,180,270} search resolves phase ambiguity correctly,
# so applying this correction is both harmful and redundant for recovery.
APPLY_PHASE_INTERCEPT = False


def _legacy_polyfit_cfo(x: np.ndarray, order: int) -> tuple[float, float]:
    """Old synchronization CFO: slope + constant-phase intercept, in rad/sample."""
    powered = x ** order
    phase = np.unwrap(np.angle(powered))
    slope, intercept = np.polyfit(np.arange(len(phase)), phase, 1)
    return float(slope / order), float(intercept / order)


def _phase_intercept_correction(y: np.ndarray, order: int) -> float:
    # Constant phase term of the powered-signal phase ramp after frequency
    # correction (polyfit intercept / order). Previously discarded; carried
    # forward so the phase offset the old estimator measured is not lost.
    phase = np.unwrap(np.angle(y ** order))
    return float(np.polyfit(np.arange(len(phase)), phase, 1)[1] / order)


def synchronize_psk(samples: np.ndarray, samples_per_symbol: int, modulation: str,
                    sample_rate: float | None = None) -> tuple[np.ndarray, dict[str, Any]]:
    """Blind PSK carrier correction plus maximum constellation-concentration timing phase.

    Returns (symbols, info). info["cfo_rad_per_sample"] is None when the shared
    quality-gated estimator refuses to lock: that None means "no reliable
    estimate" and is deliberately never coerced to a numeric 0 Hz. On refusal
    the caller still receives symbols (frequency correction skipped) with
    info["locked"] = False, so recovery may proceed and frame validation stays
    the final evidence gate. info["cfo_hz"] is filled in only when a sample
    rate is known and a lock was achieved.
    """
    order = 4 if modulation == "QPSK" else 2
    x = np.asarray(samples, dtype=np.complex64)
    if len(x) < samples_per_symbol * 16:
        raise ValueError("Recording is too short for synchronization")
    locked = True
    if USE_LEGACY_POLYFIT_CFO:
        cfo_rad_per_sample, phase_rad = _legacy_polyfit_cfo(x, order)
    else:
        # fs = 1.0 keeps the shared estimator's output in cycles/sample, so the
        # internal rad/sample conversion never depends on the true sample rate.
        cycles_per_sample = estimate_carrier_offset(x, 1.0, modulation)
        if cycles_per_sample is None:
            # NO LOCK: preserve None, skip frequency correction, and let the
            # downstream validation gate decide whether the bits are usable.
            cfo_rad_per_sample, phase_rad = None, 0.0
            locked = False
        else:
            cfo_rad_per_sample = 2 * np.pi * cycles_per_sample
            # Frequency correction first, then carry the residual constant
            # phase term (the previously-discarded polyfit intercept).
            frequency_corrected = x * np.exp(-1j * cfo_rad_per_sample * np.arange(len(x)))
            phase_rad = _phase_intercept_correction(frequency_corrected, order)
    if cfo_rad_per_sample is None:
        corrected = x
    elif APPLY_PHASE_INTERCEPT:
        corrected = x * np.exp(-1j * (cfo_rad_per_sample * np.arange(len(x)) + phase_rad))
    else:
        corrected = x * np.exp(-1j * cfo_rad_per_sample * np.arange(len(x)))
    best_offset, best_metric = 0, -np.inf
    for offset in range(samples_per_symbol):
        symbols = corrected[offset::samples_per_symbol]
        metric = abs(np.mean(symbols ** order)) / (np.mean(np.abs(symbols) ** order) + 1e-12)
        if metric > best_metric:
            best_offset, best_metric = offset, float(metric)
    info: dict[str, Any] = {
        # rad/sample (None on NO LOCK; never 0.0 as a stand-in for "unknown").
        "cfo_rad_per_sample": cfo_rad_per_sample,
        # Hz, only meaningful when a sample rate was supplied and a lock exists.
        "cfo_hz": None if cfo_rad_per_sample is None or sample_rate is None
        else cfo_rad_per_sample * sample_rate / (2 * np.pi),
        "phase_correction_rad": None if not locked and cfo_rad_per_sample is None else phase_rad,
        "timing_offset": float(best_offset),
        "timing_metric": float(best_metric),
        "locked": locked,
    }
    return corrected[best_offset::samples_per_symbol], info
