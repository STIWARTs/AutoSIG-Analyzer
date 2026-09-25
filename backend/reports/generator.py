from __future__ import annotations

import json

from backend.types import PipelineResult


def build_report(result: PipelineResult) -> str:
    accepted = result.accepted.hypothesis if result.accepted else None
    validation = result.validation
    document = {
        "input": result.analysis.signal.filename,
        "parameters": result.analysis.parameters,
        "classifier_probabilities": result.probabilities,
        # Only modulation is hypothesized and varied across candidates; the
        # recovery chain applies one fixed MVP configuration to all of them,
        # so it is reported once rather than per hypothesis.
        "fixed_recovery_configuration": {
            "interleaving": "Block",
            "fec": "Convolutional / Viterbi",
            "note": "Fixed MVP-scope configuration; not a hypothesized or searched dimension.",
        },
        "hypotheses": [{"rank": h.rank, "modulation": h.modulation, "score": h.score} for h in result.hypotheses],
        "accepted_hypothesis": ({"modulation": accepted.modulation} if accepted else None),
        "correlation_score": validation.correlation_score if validation else None,
        "header_bits": "".join(map(str, validation.header_bits)) if validation else "",
        "payload_bits": "".join(map(str, validation.payload_bits)) if validation else "",
    }
    return json.dumps(document, indent=2)
