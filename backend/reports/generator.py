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
        "hypotheses": [{"rank": h.rank, "modulation": h.modulation, "interleaving": h.interleaving,
                          "fec": h.fec, "score": h.score} for h in result.hypotheses],
        "accepted_hypothesis": ({"modulation": accepted.modulation, "interleaving": accepted.interleaving,
                                  "fec": accepted.fec} if accepted else None),
        "correlation_score": validation.correlation_score if validation else None,
        "header_bits": "".join(map(str, validation.header_bits)) if validation else "",
        "payload_bits": "".join(map(str, validation.payload_bits)) if validation else "",
    }
    return json.dumps(document, indent=2)
