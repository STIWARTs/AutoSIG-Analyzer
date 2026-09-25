from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np


@dataclass
class IngestedSignal:
    samples: np.ndarray
    sample_rate: float | None
    center_frequency: float | None
    source_format: str
    filename: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    signal: IngestedSignal
    frequency_hz: np.ndarray
    psd_db: np.ndarray
    spectrogram_frequency_hz: np.ndarray
    spectrogram_time_s: np.ndarray
    spectrogram_db: np.ndarray
    parameters: dict[str, float | None]


@dataclass(frozen=True)
class Hypothesis:
    rank: int
    modulation: str
    interleaving: str
    fec: str
    score: float


@dataclass
class RecoveryAttempt:
    hypothesis: Hypothesis
    steps: list[tuple[str, str, str]]
    recovered_bits: np.ndarray | None = None
    error: str | None = None
    # Carrier/timing/phase-corrected symbols captured at the synchronization
    # step (before demodulation collapses them to bits). Exposed so the UI can
    # render a "recovered symbols" constellation as evidence of the sync stage.
    synchronized_symbols: np.ndarray | None = None
    # Resolved carrier phase state in degrees chosen by the demodulation
    # ambiguity search (QPSK: 0/90/180/270, BPSK: 0/180). None until the
    # demodulation step has run.
    phase_state_degrees: float | None = None


@dataclass
class ValidationResult:
    passed: bool
    correlation_score: float
    peak_index: int
    header_bits: np.ndarray
    payload_bits: np.ndarray


@dataclass
class PipelineResult:
    analysis: AnalysisResult
    probabilities: dict[str, float]
    hypotheses: list[Hypothesis]
    attempts: list[RecoveryAttempt]
    validation: ValidationResult | None
    accepted: RecoveryAttempt | None
