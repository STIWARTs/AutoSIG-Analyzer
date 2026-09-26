# -*- coding: utf-8 -*-
"""Pure payload-correctness scoring for the Step 3 evaluation.

No file I/O and no pipeline execution live here, so the alignment, BER, and
aggregation logic is unit-testable in isolation. The classification of an
attempt onto the modulation the *generator actually used* (not the one the app
"accepted") and the integrity gating are the caller's job; this module only
answers, given recovered bits and a trusted ground truth, how many payload bits
came back right.
"""
from __future__ import annotations

from typing import Any

import numpy as np

from backend.eval.ground_truth import (FRAME_BITS, PAYLOAD_BITS, SYNC_BITS,
                                       CaptureTruth)
from backend.recovery.coding import HEADER, PREAMBLE

# The fixed 64-bit pattern that precedes every payload; used purely to anchor
# the logical start of the frame, exactly like the production validator does.
_SYNC_PATTERN = np.concatenate((PREAMBLE, HEADER)).astype(np.uint8)

# A sync-correlation score below this means the anchor is not trustworthy and
# any BER computed from it would be misleading -- we still record the number but
# flag the capture so it is not silently taken as a real measurement.
SYNC_SANITY = 0.90

# Payload outcome ladder (mutually exclusive, ordered by increasing success).
OUTCOME_RECOVERY_FAILED = "RECOVERY_FAILED"
OUTCOME_NO_COMPARABLE_BITS = "NO_COMPARABLE_BITS"
OUTCOME_PARTIAL = "PARTIAL"
OUTCOME_FULL = "FULL"
OUTCOME_PERFECT = "PERFECT"


def correlate_sync(recovered: np.ndarray) -> tuple[int, float]:
    """Locate the PREAMBLE+HEADER anchor in the recovered bitstream.

    Mirrors backend.validation.correlation's ±1 correlate (int16 cast first so
    uint8 subtraction cannot wrap a 0 bit to 255). Returns (peak_index, score)
    where score is peak/SYNC_BITS in [-1, 1]; (0, 0.0) if too short to anchor.
    """
    bits = np.asarray(recovered, dtype=np.uint8)
    if len(bits) < len(_SYNC_PATTERN):
        return 0, 0.0
    signal = bits.astype(np.int16) * 2 - 1
    reference = _SYNC_PATTERN.astype(np.int16) * 2 - 1
    correlation = np.correlate(signal, reference, mode="valid")
    peak_index = int(np.argmax(correlation))
    return peak_index, float(correlation[peak_index] / len(reference))


def score_capture(recovered_bits: np.ndarray | None, truth: CaptureTruth) -> dict[str, Any]:
    """Score one ground-truth-verified capture. Assumes the caller ran the
    integrity gate and it passed; this function does not re-verify provenance.

    Payload is compared only over bits present in BOTH the recovered stream and
    the known payload -- missing bits are never credited as correct nor counted
    as errors; instead they shrink ``comparable_bits`` and demote the outcome to
    PARTIAL. A null/empty recovery is RECOVERY_FAILED, not BER 0.
    """
    record: dict[str, Any] = {
        "outcome": None,
        "recovered_len": None,
        "true_payload_bits": PAYLOAD_BITS,
        "payload_comparable": 0,
        "payload_errors": None,
        "payload_ber": None,
        "payload_accuracy": None,
        "payload_length_match": False,
        "frame_comparable": 0,
        "frame_errors": None,
        "frame_accuracy": None,
        "alignment_offset": None,
        "sync_score": None,
        "alignment_anomaly": False,
    }

    if recovered_bits is None:
        record["outcome"] = OUTCOME_RECOVERY_FAILED
        return record
    recovered = np.asarray(recovered_bits, dtype=np.uint8)
    record["recovered_len"] = int(len(recovered))
    if len(recovered) < len(_SYNC_PATTERN):
        record["outcome"] = OUTCOME_NO_COMPARABLE_BITS
        return record

    pk, sync_score = correlate_sync(recovered)
    record["alignment_offset"] = pk
    record["sync_score"] = sync_score
    record["alignment_anomaly"] = bool(pk != 0 or sync_score < SYNC_SANITY)

    # Payload region: truth starts at SYNC_BITS in the frame; recovered payload
    # starts at pk + SYNC_BITS. Compare only the overlapping window.
    recovered_payload = recovered[pk + SYNC_BITS: pk + SYNC_BITS + PAYLOAD_BITS]
    comparable = int(min(len(recovered_payload), PAYLOAD_BITS))
    record["payload_comparable"] = comparable
    record["payload_length_match"] = bool(comparable == PAYLOAD_BITS)
    if comparable <= 0:
        record["outcome"] = OUTCOME_NO_COMPARABLE_BITS
    else:
        errors = int(np.count_nonzero(recovered_payload[:comparable] != truth.payload[:comparable]))
        record["payload_errors"] = errors
        record["payload_ber"] = errors / comparable
        record["payload_accuracy"] = 1.0 - (errors / comparable)
        if comparable == PAYLOAD_BITS:
            record["outcome"] = OUTCOME_PERFECT if errors == 0 else OUTCOME_FULL
        else:
            record["outcome"] = OUTCOME_PARTIAL

    # Frame-level comparison is secondary and reported as sync-bits-inflated.
    recovered_frame = recovered[pk: pk + FRAME_BITS]
    frame_comparable = int(min(len(recovered_frame), FRAME_BITS))
    record["frame_comparable"] = frame_comparable
    if frame_comparable > 0:
        frame_errors = int(np.count_nonzero(recovered_frame[:frame_comparable] != truth.frame[:frame_comparable]))
        record["frame_errors"] = frame_errors
        record["frame_accuracy"] = 1.0 - (frame_errors / frame_comparable)
    return record


def _rate(numerator: float, denominator: float) -> float | None:
    return (numerator / denominator) if denominator else None


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate an already-classified record set (one per capture per input).

    Only captures that reached a comparable-bit state feed BER; failures carry
    null BER and are counted in status buckets, never averaged in as zero. Every
    ratio is accompanied by its explicit denominators.
    """
    scored = [r for r in records if r.get("payload_comparable", 0) > 0]
    total_compared = sum(r["payload_comparable"] for r in scored)
    total_errors = sum(r["payload_errors"] or 0 for r in scored)
    per_file_ber = [r["payload_ber"] for r in scored if r["payload_ber"] is not None]

    outcomes: dict[str, int] = {}
    for r in records:
        key = r.get("outcome") or r.get("classification") or "UNCLASSIFIED"
        outcomes[key] = outcomes.get(key, 0) + 1

    return {
        "captures": len(records),
        "scored_captures": len(scored),
        "payload_bits_compared": int(total_compared),
        "payload_bit_errors": int(total_errors),
        "micro_ber": _rate(total_errors, total_compared),
        "macro_ber": (sum(per_file_ber) / len(per_file_ber)) if per_file_ber else None,
        "perfect_payload_recoveries": outcomes.get(OUTCOME_PERFECT, 0),
        "outcome_counts": outcomes,
    }
