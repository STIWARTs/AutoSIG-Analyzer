# -*- coding: utf-8 -*-
"""Tests for the Step 3 payload ground-truth evaluation layer.

These verify the evaluator machinery itself: deterministic reconstruction,
the IQ-identity integrity gate on representative real captures, alignment,
BER math, and the failure semantics. No test here asserts anything about how
the full corpus scores as a whole -- that is the tool's job at run time.
"""
from pathlib import Path

import numpy as np
import pytest

from backend.eval.ground_truth import (FRAME_BITS, PAYLOAD_BITS, SYNC_BITS,
                                       build_corpus_truth, key_from_filename,
                                       verify_iq_identity)
from backend.eval.payload_metrics import aggregate, score_capture
from backend.recovery.coding import HEADER, PREAMBLE

DATASETS = Path(__file__).resolve().parents[1] / "datasets"


@pytest.fixture(scope="module")
def truths():
    return build_corpus_truth()


def test_reconstruction_is_deterministic(truths):
    again = build_corpus_truth()
    assert set(again) == set(truths)
    for key, truth in truths.items():
        assert np.array_equal(again[key].payload, truth.payload)
        assert again[key].frequency_offset_hz == truth.frequency_offset_hz


def test_expected_lengths_and_fixed_sync_region(truths):
    truth = truths["qpsk_000"]
    assert len(truth.payload) == PAYLOAD_BITS == 128
    assert len(truth.frame) == FRAME_BITS == 192
    assert np.array_equal(truth.frame[:SYNC_BITS], np.concatenate((PREAMBLE, HEADER)))
    assert np.array_equal(truth.frame[SYNC_BITS:], truth.payload)


def test_filename_key_mapping():
    assert key_from_filename("qpsk_000_snr-2_cfo-74.iq") == "qpsk_000"
    assert key_from_filename("bpsk_031_snr+0_cfo+68.wav") == "bpsk_031"


def test_manifest_agrees_with_replay(truths):
    import json
    manifest = json.loads((DATASETS / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest:
        truth = truths[key_from_filename(entry["iq"])]
        assert float(entry["frequency_offset_hz"]) == truth.frequency_offset_hz
        assert float(entry["snr_db"]) == truth.snr_db
        assert entry["label"] == truth.modulation


@pytest.mark.skipif(not DATASETS.exists(), reason="corpus not present")
def test_iq_identity_gate_passes_for_representative_captures(truths):
    import json
    manifest = json.loads((DATASETS / "manifest.json").read_text(encoding="utf-8"))
    for wanted in ("qpsk_000", "bpsk_000", "qpsk_023"):
        entry = next(e for e in manifest if key_from_filename(e["iq"]) == wanted)
        result = verify_iq_identity(truths[wanted], DATASETS / entry["iq"])
        assert result["ok"], (wanted, result)


def test_score_perfect_recovery(truths):
    truth = truths["qpsk_000"]
    record = score_capture(truth.frame.copy(), truth)
    assert record["outcome"] == "PERFECT"
    assert record["payload_errors"] == 0 and record["payload_ber"] == 0.0
    assert record["payload_comparable"] == PAYLOAD_BITS
    assert record["alignment_offset"] == 0 and not record["alignment_anomaly"]


def test_score_full_with_bit_errors(truths):
    truth = truths["bpsk_005"]
    recovered = truth.frame.copy()
    recovered[SYNC_BITS:SYNC_BITS + 3] ^= 1  # flip exactly 3 payload bits
    record = score_capture(recovered, truth)
    assert record["outcome"] == "FULL"
    assert record["payload_errors"] == 3
    assert record["payload_ber"] == pytest.approx(3 / 128)
    assert record["payload_accuracy"] == pytest.approx(1 - 3 / 128)


def test_score_partial_truncation_is_not_credited_or_penalized(truths):
    truth = truths["qpsk_010"]
    recovered = truth.frame[: SYNC_BITS + 100]  # last 28 payload bits missing
    record = score_capture(recovered, truth)
    assert record["outcome"] == "PARTIAL"
    assert record["payload_comparable"] == 100
    assert record["payload_errors"] == 0
    assert not record["payload_length_match"]


def test_score_missing_and_short_recoveries(truths):
    truth = truths["qpsk_000"]
    assert score_capture(None, truth)["outcome"] == "RECOVERY_FAILED"
    assert score_capture(np.array([], dtype=np.uint8), truth)["outcome"] == "NO_COMPARABLE_BITS"
    assert score_capture(np.zeros(50, dtype=np.uint8), truth)["outcome"] == "NO_COMPARABLE_BITS"


def test_score_shifted_alignment_is_detected_not_silently_miscompared(truths):
    truth = truths["qpsk_000"]
    rng = np.random.default_rng(1)
    recovered = np.concatenate((rng.integers(0, 2, 8, dtype=np.uint8), truth.frame))
    record = score_capture(recovered, truth)
    assert record["alignment_offset"] == 8
    assert record["alignment_anomaly"]  # unexpected offset must be flagged
    assert record["payload_errors"] == 0  # but the anchored comparison is still valid


def test_aggregate_never_treats_failures_as_zero_ber(truths):
    truth = truths["qpsk_000"]
    rows = [
        score_capture(truth.frame.copy(), truth),                      # PERFECT
        score_capture(np.concatenate((truth.frame[:SYNC_BITS], truth.frame[SYNC_BITS:] ^ 1)), truth),  # all 128 flipped
        score_capture(None, truth),                                    # RECOVERY_FAILED
    ]
    rows[1]["outcome"] = "FULL"  # (score_capture already sets FULL; keep explicit)
    agg = aggregate(rows)
    assert agg["captures"] == 3 and agg["scored_captures"] == 2
    assert agg["payload_bits_compared"] == 256 and agg["payload_bit_errors"] == 128
    assert agg["micro_ber"] == pytest.approx(0.5)   # failures excluded, not zeroed in
    assert agg["macro_ber"] == pytest.approx(0.5)   # mean(0.0, 1.0)
    assert agg["outcome_counts"]["RECOVERY_FAILED"] == 1
    assert agg["perfect_payload_recoveries"] == 1
