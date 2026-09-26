# -*- coding: utf-8 -*-
"""Step 3 offline evaluation: does the SPECTRA pipeline recover the true payload bits?

Evaluates the *existing* production pipeline (run_pipeline, unchanged) against
deterministically reconstructed corpus ground truth, gated by a per-capture
IQ bit-identity check. This tool writes only its report JSON; it never touches
the dataset, the manifest, or any production module.

Interpretation limits (must travel with any use of these numbers):
this measures internal synthetic-corpus recovery performance ONLY. The corpus
is AWGN + CFO, rectangular pulses, fixed 6000 baud, zero timing offset, zero
initial phase offset, fixed FEC/interleaving, and one reused noise realization.
It does not establish real-world/off-air accuracy, timing or phase recovery
quality, FEC identification, multipath performance, or generalization.

Usage:
    python tools/corpus_payload_eval.py                 # full corpus, IQ+WAV
    python tools/corpus_payload_eval.py --limit 8       # smoke run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.eval.ground_truth import (build_corpus_truth, key_from_filename,
                                       verify_iq_identity)
from backend.eval.payload_metrics import aggregate, score_capture
from backend.ingestion.parser import load_iq, load_wav
from backend.pipeline import run_pipeline

OUTCOME_NOT_ATTEMPTED = "NOT_ATTEMPTED"
OUTCOME_GROUND_TRUTH_MISMATCH = "GROUND_TRUTH_MISMATCH"


def evaluate_capture(entry: dict, truth, datasets: Path, top_k: int, inputs: list[str]) -> list[dict]:
    """Return one record row per requested input (iq/wav) for a single capture."""
    integrity = verify_iq_identity(truth, datasets / entry["iq"])
    reasons = []
    if not integrity["ok"]:
        reasons.append(f"iq identity failed (max_abs_diff={integrity['max_abs_diff']}, "
                       f"len {integrity['reproduced_len']} vs {integrity['on_disk_len']})")
    if float(entry["frequency_offset_hz"]) != truth.frequency_offset_hz:
        reasons.append("manifest frequency_offset_hz != replayed RNG draw")
    if float(entry["snr_db"]) != truth.snr_db:
        reasons.append("manifest snr_db != replayed SNR cycle value")
    if entry["label"] != truth.modulation:
        reasons.append("manifest label != replayed modulation")

    rows = []
    for input_kind in inputs:
        base = {
            "key": truth.key, "modulation": truth.modulation, "snr_db": truth.snr_db,
            "true_offset_hz": truth.frequency_offset_hz, "input": input_kind,
            "file": entry[input_kind],
            "integrity_ok": integrity["ok"] and not reasons,
            "integrity_detail": integrity,
        }
        if base["integrity_ok"] is not True:
            base.update({"outcome": OUTCOME_GROUND_TRUTH_MISMATCH, "integrity_reasons": reasons,
                         "payload_comparable": 0, "payload_errors": None, "payload_ber": None})
            rows.append(base)
            continue
        try:
            signal = (load_iq(datasets / entry["iq"], datasets / f"{Path(entry['iq']).stem}.sigmf-meta", entry["iq"])
                      if input_kind == "iq" else load_wav(datasets / entry["wav"], entry["wav"]))
            result = run_pipeline(signal, top_k=top_k)
        except Exception as exc:  # the evaluator must not die on one capture
            base.update({"outcome": "RECOVERY_FAILED", "error": f"pipeline raised: {exc}",
                         "payload_comparable": 0, "payload_errors": None, "payload_ber": None})
            rows.append(base)
            continue

        # Ground-truth keying: the attempt whose hypothesized modulation equals
        # the modulation the GENERATOR used. Never result.accepted (that is
        # application validation, not correctness).
        true_attempt = next((a for a in result.attempts if a.hypothesis.modulation == truth.modulation), None)
        flags = {
            "hypotheses": [a.hypothesis.modulation for a in result.attempts],
            "no_lock": False, "frame_validation": None, "accepted_modulation": None,
        }
        if result.accepted is not None:
            flags["accepted_modulation"] = result.accepted.hypothesis.modulation
        if true_attempt is not None:
            flags["no_lock"] = any(s[0] == "Synchronization" and s[1] == "WARN" for s in true_attempt.steps)
            fv = next((s[1] for s in true_attempt.steps if s[0] == "Frame Validation"), None)
            flags["frame_validation"] = fv
            record = score_capture(true_attempt.recovered_bits, truth)
        else:
            record = {"outcome": OUTCOME_NOT_ATTEMPTED, "payload_comparable": 0, "payload_errors": None,
                      "payload_ber": None, "payload_accuracy": None, "recovered_len": None,
                      "alignment_offset": None, "sync_score": None, "alignment_anomaly": False,
                      "frame_comparable": 0, "frame_errors": None, "frame_accuracy": None,
                      "payload_length_match": False, "true_payload_bits": len(truth.payload)}
        base.update(record)
        base.update(flags)
        rows.append(base)
    return rows


def breakdown(rows: list[dict], field: str) -> dict:
    out = {}
    for value in sorted({str(r[field]) for r in rows}):
        subset = [r for r in rows if str(r[field]) == value]
        out[value] = aggregate(subset)
        out[value]["frame_validation_passes"] = sum(1 for r in subset if r.get("frame_validation") == "PASS")
        out[value]["no_lock_count"] = sum(1 for r in subset if r.get("no_lock"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets-dir", type=Path, default=ROOT / "datasets")
    parser.add_argument("--output", type=Path, default=ROOT / "tools" / "corpus_payload_report.json")
    parser.add_argument("--top-k", type=int, default=2, help="production pipeline default is 2")
    parser.add_argument("--limit", type=int, default=0, help="evaluate first N captures (0 = all)")
    parser.add_argument("--inputs", default="iq,wav")
    args = parser.parse_args()
    inputs = [i.strip().lower() for i in args.inputs.split(",") if i.strip()]

    manifest = json.loads((args.datasets_dir / "manifest.json").read_text(encoding="utf-8"))
    truths = build_corpus_truth()
    entries = manifest[: args.limit] if args.limit else manifest

    rows: list[dict] = []
    for i, entry in enumerate(entries, 1):
        key = key_from_filename(entry["iq"])
        truth = truths.get(key)
        if truth is None:
            print(f"[{i:3d}/{len(entries)}] {entry['iq']}: UNKNOWN CAPTURE KEY {key}")
            continue
        capture_rows = evaluate_capture(entry, truth, args.datasets_dir, args.top_k, inputs)
        rows.extend(capture_rows)
        summary = " | ".join(f"{r['input'].upper()}:{r['outcome']}" for r in capture_rows)
        print(f"[{i:3d}/{len(entries)}] {entry['iq']}: {summary}", flush=True)

    report: dict = {
        "metadata": {
            "purpose": "Step 3 synthetic-corpus payload ground-truth evaluation (offline, evaluation-only).",
            "pipeline": f"backend.pipeline.run_pipeline(top_k={args.top_k}), unchanged production code",
            "ground_truth": "deterministic replay of training/generate_dataset.py (seed 20260922), "
                            "gated per-capture by IQ bit-identity vs the on-disk file",
            "corpus_generator_note": "The shipped corpus was produced by the NumPy flowgraph-equivalent "
                                     "fallback, NOT by GNU Radio; the identity gate re-runs that same fallback.",
            "attempt_selection": "attempt whose hypothesis matches the TRUE modulation (never 'accepted')",
            "interpretation_limits": [
                "Measures internal synthetic-corpus recovery performance only.",
                "Does NOT establish real-world or off-air accuracy.",
                "Does NOT test FEC/interleaver identification (single fixed scheme).",
                "Does NOT test timing recovery (true timing offset is always 0).",
                "Does NOT test phase recovery breadth (true initial phase is always 0).",
                "No pulse shaping, single symbol rate, AWGN+CFO channel only.",
                "All captures share one reused noise realization -> per-SNR points are single trials.",
                "Preamble/frame validation and payload correctness are DIFFERENT metrics; a frame-validation "
                "PASS does not mean the payload was recovered correctly, and vice versa.",
            ],
        },
        "integrity_summary": {
            "captures": len(entries),
            "iq_identity_verified": sum(1 for r in rows if r["input"] == inputs[0] and r["integrity_ok"]),
            "ground_truth_mismatches": sum(1 for r in rows if r["outcome"] == OUTCOME_GROUND_TRUTH_MISMATCH),
        },
        "per_capture": rows,
        "aggregates": {},
    }
    for input_kind in inputs:
        subset = [r for r in rows if r["input"] == input_kind]
        agg = aggregate(subset)
        agg["classification_coverage"] = sum(1 for r in subset if r["outcome"] != OUTCOME_NOT_ATTEMPTED
                                             and r["outcome"] != OUTCOME_GROUND_TRUTH_MISMATCH)
        agg["frame_validation_passes"] = sum(1 for r in subset if r.get("frame_validation") == "PASS")
        agg["no_lock_count"] = sum(1 for r in subset if r.get("no_lock"))
        agg["alignment_anomalies"] = sum(1 for r in subset if r.get("alignment_anomaly"))
        agg["by_modulation"] = breakdown(subset, "modulation")
        agg["by_snr_db"] = breakdown(subset, "snr_db")
        report["aggregates"][input_kind] = agg

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"\nReport: {args.output}")
    for input_kind in inputs:
        agg = report["aggregates"][input_kind]
        print(f"--- {input_kind.upper()} ---")
        print(f"captures={agg['captures']} scored={agg['scored_captures']} "
              f"bits_compared={agg['payload_bits_compared']} errors={agg['payload_bit_errors']}")
        print(f"micro BER={agg['micro_ber'] if agg['micro_ber'] is None else round(agg['micro_ber'], 6)} "
              f"macro BER={agg['macro_ber'] if agg['macro_ber'] is None else round(agg['macro_ber'], 6)} "
              f"perfect={agg['perfect_payload_recoveries']} "
              f"frame_validation_passes={agg['frame_validation_passes']} (different metric!)")
        print(f"outcomes={agg['outcome_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
