from __future__ import annotations

from backend.dsp.analysis import analyze_signal, prepare_samples
from backend.hypotheses.engine import build_hypotheses
from backend.ml.classifier import classify_samples
from backend.recovery.chain import run_recovery
from backend.types import IngestedSignal, PipelineResult
from backend.validation.correlation import validate_bitstream


def run_pipeline(signal_data: IngestedSignal, top_k: int = 2) -> PipelineResult:
    # Classify first (same pre-processed samples as before) so the DSP analysis
    # can pick the noise-optimal carrier-offset estimator order for the modulations.
    probabilities = classify_samples(prepare_samples(signal_data))
    analysis = analyze_signal(signal_data, modulation=max(probabilities, key=probabilities.get))
    hypotheses = build_hypotheses(probabilities, top_k=top_k)
    attempts = []
    accepted = None
    validations: dict[int, object] = {}
    for hypothesis in hypotheses:
        # Every ranked hypothesis is pushed through the full chain, even after
        # one is accepted: rejected attempts must stay visible on the Recovery
        # screen so a reviewer sees the AI prediction being tested and refuted.
        attempt = run_recovery(analysis.signal.samples, hypothesis)
        attempts.append(attempt)
        if attempt.recovered_bits is None:
            continue
        validations[hypothesis.rank] = validate_bitstream(attempt.recovered_bits)
        attempt.steps.append(("Frame Validation", "PASS" if validations[hypothesis.rank].passed else "FAIL",
                              f"Correlation {validations[hypothesis.rank].correlation_score:.3f}"))
        if validations[hypothesis.rank].passed and accepted is None:
            accepted = attempt
    if accepted:
        validation = validations[accepted.hypothesis.rank]
    elif validations:
        # Nothing passed; expose the best-scoring attempt, not merely the
        # highest-ranked (last-tried, typically weakest) one.
        validation = max(validations.values(), key=lambda v: v.correlation_score)
    else:
        validation = None
    return PipelineResult(analysis, probabilities, hypotheses, attempts, validation, accepted)
