from __future__ import annotations

import numpy as np
from scipy import signal

from backend.dsp.carrier import estimate_carrier_offset
from backend.types import AnalysisResult, IngestedSignal

# Shared with the recovery synchronization path (backend.dsp.sync): one gated
# estimator for both display and correction, imported here under the historical
# private name so existing callers and A/B tooling keep working.
_estimate_carrier_offset = estimate_carrier_offset


def _occupied_bandwidth(freq: np.ndarray, psd: np.ndarray) -> float:
    floor = np.percentile(psd, 20)
    mask = psd > floor + 6.0
    if not np.any(mask):
        return 0.0
    selected = freq[mask]
    return float(selected.max() - selected.min())


def _estimate_snr(psd: np.ndarray) -> float:
    noise = np.percentile(psd, 20)
    signal_level = np.percentile(psd, 90)
    return float(max(signal_level - noise, 0.0))


def _estimate_symbol_rate(x: np.ndarray, fs: float | None) -> float | None:
    # Fourth-power removes QPSK data modulation and exposes periodic symbol structure.
    y = x[: min(len(x), 32768)] ** 4
    if len(y) < 128:
        return None
    if fs is None:
        return None
    spectrum = np.abs(np.fft.fft(y * np.hanning(len(y))))
    frequencies = np.fft.fftfreq(len(y), 1 / fs)
    candidates = (frequencies > fs / 200) & (frequencies < fs / 2.2)
    if not np.any(candidates):
        return None
    return float(frequencies[candidates][np.argmax(spectrum[candidates])])


def prepare_samples(signal_data: IngestedSignal, remove_dc: bool = True) -> np.ndarray:
    x = np.asarray(signal_data.samples, dtype=np.complex64)
    if remove_dc:
        x = x - np.mean(x)
    return x


def analyze_signal(signal_data: IngestedSignal, remove_dc: bool = True,
                   modulation: str | None = None) -> AnalysisResult:
    x = prepare_samples(signal_data, remove_dc)
    processed = IngestedSignal(samples=x, sample_rate=signal_data.sample_rate,
                               center_frequency=signal_data.center_frequency,
                               source_format=signal_data.source_format, filename=signal_data.filename,
                               metadata=signal_data.metadata)
    nperseg = min(2048, max(64, len(x)))
    # SciPy's default fs=1 keeps spectral shape meaningful in cycles/sample
    # when raw IQ has no trustworthy rate metadata.
    display_fs = processed.sample_rate if processed.sample_rate is not None else 1.0
    freq, psd = signal.welch(x, fs=display_fs, nperseg=nperseg,
                             return_onesided=False, scaling="density")
    order = np.argsort(freq)
    freq, psd = freq[order], psd[order]
    psd_db = 10 * np.log10(np.maximum(psd, 1e-14))
    f_spec, t_spec, sxx = signal.stft(x, fs=display_fs, nperseg=min(512, nperseg),
                                      return_onesided=False)
    f_order = np.argsort(f_spec)
    sxx_db = 20 * np.log10(np.maximum(np.abs(sxx[f_order]), 1e-10))
    has_rate = processed.sample_rate is not None
    # Synthetic baseband captures carry core:frequency 0.0 (or nothing at all for
    # WAV), so echoing metadata alone reads as "0.0 / UNAVAILABLE". Measure the
    # carrier offset from the signal itself and anchor it to the metadata center
    # when one exists; without a sample rate the value stays relative, so it is
    # withheld from the Hz-denominated parameters.
    carrier_offset = _estimate_carrier_offset(x, processed.sample_rate, modulation)
    # A genuine absolute RF anchor exists only when the capture carries a
    # nonzero center frequency (SigMF core:frequency or manual entry). Every
    # synthetic baseband file ships 0.0 as a placeholder, which must not read
    # as "absolute RF known".
    absolute_available = (processed.center_frequency is not None
                          and float(processed.center_frequency) != 0.0)
    center = (processed.center_frequency or 0.0) + carrier_offset if carrier_offset is not None else None
    parameters = {
        "sample_rate_hz": processed.sample_rate if has_rate else None,
        "occupied_bandwidth_hz": _occupied_bandwidth(freq, psd_db) if has_rate else None,
        "center_frequency_hz": center,
        "carrier_offset_hz": carrier_offset,
        "estimated_snr_db": _estimate_snr(psd_db),
        "estimated_symbol_rate_baud": _estimate_symbol_rate(x, processed.sample_rate),
        "absolute_frequency_available": float(absolute_available),
    }
    return AnalysisResult(processed, freq, psd_db, f_spec[f_order], t_spec, sxx_db, parameters)
