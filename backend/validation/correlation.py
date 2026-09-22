from __future__ import annotations

import numpy as np

from backend.recovery.coding import PREAMBLE
from backend.types import ValidationResult


def validate_bitstream(bits: np.ndarray, threshold: float = 0.90, header_length: int = 64) -> ValidationResult:
    recovered = np.asarray(bits, dtype=np.uint8)
    if len(recovered) < len(PREAMBLE):
        return ValidationResult(False, 0.0, -1, np.array([], dtype=np.uint8), np.array([], dtype=np.uint8))
    # Cast before arithmetic: uint8 subtraction would turn a 0 bit into 255.
    signal = recovered.astype(np.int16) * 2 - 1
    reference = PREAMBLE.astype(np.int16) * 2 - 1
    correlation = np.correlate(signal, reference, mode="valid")
    peak_index = int(np.argmax(correlation))
    score = float(correlation[peak_index] / len(reference))
    end_header = min(len(recovered), peak_index + header_length)
    return ValidationResult(score >= threshold, score, peak_index,
                            recovered[peak_index:end_header], recovered[end_header:])
