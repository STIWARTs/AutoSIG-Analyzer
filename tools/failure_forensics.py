# -*- coding: utf-8 -*-
"""Step 4 read-only failure forensics: where does the information go wrong?

Instruments every non-perfect IQ capture by re-walking the EXACT production
recovery steps (backend.recovery.chain internals replicated with the same
imports — no production code is modified or even aware of this tool) and
measuring each intermediate stage against the deterministic ground truth:

    CFO estimate -> frequency correction -> symbol extraction
    -> hard demodulation -> de-interleave -> Viterbi -> frame alignment -> payload

Writes tools/failure_forensics.json + a console summary. Touches nothing else.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.dsp.carrier import estimate_carrier_offset
from backend.dsp.sync import synchronize_psk
from backend.eval.ground_truth import SYNC_BITS, build_corpus_truth
from backend.eval.payload_metrics import correlate_sync
from backend.ingestion.parser import load_iq
from backend.pipeline import run_pipeline  # used only for the qpsk_002 deep-dive
from backend.recovery.chain import _bpsk_demodulate, _qpsk_demodulate
from backend.recovery.coding import block_deinterleave, viterbi_decode
from backend.dsp.analysis import prepare_samples
from backend.validation.correlation import validate_bitstream

DATASETS = ROOT / "datasets"
FS = 48_000.0


def trace_capture(x: np.ndarray, truth) -> dict:
    """Replicate run_recovery's path for the true modulation, measuring every stage."""
    modulation = truth.modulation
    out: dict = {"modulation": modulation, "snr_db": truth.snr_db, "true_cfo_hz": truth.frequency_offset_hz}

    # --- stage 1: CFO estimation (same shared estimator production uses)
    est_hz = estimate_carrier_offset(x, FS, modulation)
    out["cfo_est_hz"] = est_hz
    out["cfo_err_hz"] = None if est_hz is None else est_hz - truth.frequency_offset_hz

    # --- stage 2/3: production synchronization (sample_rate arg only adds cfo_hz metadata)
    symbols, sync = synchronize_psk(x, 8, modulation, sample_rate=FS)
    out["locked"] = bool(sync["locked"])
    out["timing_offset"] = sync["timing_offset"]
    out["timing_metric"] = sync["timing_metric"]
    out["n_symbols"] = int(len(symbols))

    # --- stage 4/5: demodulation with the chain's exact phase grid
    demod = _qpsk_demodulate if modulation == "QPSK" else _bpsk_demodulate
    bps = 2 if modulation == "QPSK" else 1
    phase_angles = ([0.0, np.pi / 2, np.pi, 3 * np.pi / 2] if modulation == "QPSK" else [0.0, np.pi])
    n_bits = len(symbols) * bps
    block = n_bits - n_bits % 12
    keep = block - (block % 2)
    out["chain_tail_dropped_bits"] = int(n_bits - keep)
    candidates = []
    hard_all = {}
    for phase_index, angle in enumerate(phase_angles):
        hard = demod(symbols * np.exp(-1j * angle))[:keep]
        decoded = viterbi_decode(block_deinterleave(hard), terminated=True)
        score = validate_bitstream(decoded, threshold=-1).correlation_score
        candidates.append((score, phase_index))
        hard_all[phase_index] = hard
    best_score, best_index = max(candidates, key=lambda item: item[0])
    hard = hard_all[best_index]
    decoded = viterbi_decode(block_deinterleave(hard), terminated=True)
    out["chain_selected_phase_index"] = best_index
    out["chain_internal_score"] = float(best_score)  # what the chain itself "sees"

    # --- stage measurements vs ground truth (positional, no shifting tricks)
    tl = truth.interleaved
    hard_err = int(np.count_nonzero(hard != tl[:len(hard)])) if len(hard) else 0
    out["hard_bits_len"] = int(len(hard))
    out["hard_bit_errors_pos"] = hard_err
    out["hard_bit_ber_pos"] = hard_err / len(hard) if len(hard) else None
    first = np.flatnonzero(hard != tl[:len(hard)])
    out["hard_first_error_index"] = int(first[0]) if len(first) else None
    out["hard_error_count"] = int(len(first))
    # how good is the BEST possible phase (upper bound demod could achieve)?
    best_phase_err = min(int(np.count_nonzero(hard_all[i] != tl[:len(hard_all[i])])) for i in hard_all)
    out["hard_bit_errors_best_phase"] = best_phase_err

    coded = block_deinterleave(hard)
    ce = int(np.count_nonzero(coded != truth.encoded[:len(coded)]))
    out["coded_bit_errors_pos"] = ce
    out["coded_bit_len"] = int(len(coded))

    out["decoded_len"] = int(len(decoded))
    out["true_frame_len"] = int(len(truth.frame))
    pe = int(np.count_nonzero(decoded != truth.frame[:len(decoded)]))
    out["frame_errors_from_index0"] = pe

    # --- stage 6: the Step-3 anchor comparison (must reproduce step-3 numbers)
    pk, sync_score = correlate_sync(decoded)
    out["align_pk"] = pk
    out["align_sync64_score"] = sync_score
    payload = decoded[pk + SYNC_BITS: pk + SYNC_BITS + 128]
    comp = len(payload)
    errs = int(np.count_nonzero(payload != truth.payload[:comp])) if comp else 0
    out["payload_comparable"] = comp
    out["payload_errors"] = errs if comp else None
    out["payload_ber"] = errs / comp if comp else None
    out["payload_perfect"] = bool(comp == 128 and errs == 0)

    # --- stage 7: production validator on this attempt (32-bit preamble, 0.90)
    val = validate_bitstream(decoded)
    out["validator_score32"] = val.correlation_score
    out["validator_peak"] = val.peak_index
    out["validator_passed"] = bool(val.passed)

    # head/tail structure of remaining errors (diagnostic shapes)
    if comp and errs:
        idx = np.flatnonzero(payload != truth.payload[:comp])
        out["payload_error_first"] = int(idx[0]); out["payload_error_last"] = int(idx[-1])
    return out


def main() -> int:
    manifest = json.loads((DATASETS / "manifest.json").read_text(encoding="utf-8"))
    truths = build_corpus_truth()
    step3 = json.loads((ROOT / "tools" / "corpus_payload_report.json").read_text(encoding="utf-8"))
    step3_iq = {r["key"]: r for r in step3["per_capture"] if r["input"] == "iq"}

    results = {}
    for i, entry in enumerate(manifest, 1):
        key = "_".join(entry["iq"].split("_")[:2])
        truth = truths[key]
        sig = load_iq(DATASETS / entry["iq"], DATASETS / f"{Path(entry['iq']).stem}.sigmf-meta", entry["iq"])
        x = prepare_samples(sig)
        r = trace_capture(x, truth)
        r["step3_outcome"] = step3_iq[key]["outcome"]
        r["step3_frame_validation"] = step3_iq[key].get("frame_validation")
        # cross-check: the trace must reproduce the Step-3 measurement
        r["matches_step3"] = (r["payload_comparable"] == step3_iq[key].get("payload_comparable")
                              and (r["payload_errors"] or 0) == (step3_iq[key].get("payload_errors") or 0))
        results[key] = r
        flag = "" if r["payload_perfect"] else "  <-- IMPERFECT"
        print(f"[{i:2d}/64] {key} {truth.modulation} snr{truth.snr_db:+.0f} "
              f"{'OK ' if r['payload_perfect'] else 'ERR'} ber={r['payload_ber'] if r['payload_ber'] is None else round(r['payload_ber'],4)} "
              f"locked={r['locked']} cfoErr={None if r['cfo_err_hz'] is None else round(r['cfo_err_hz'],2)}Hz "
              f"tailDrop={r['chain_tail_dropped_bits']}{flag}", flush=True)

    # qpsk_002 deep-dive through the REAL pipeline object graph (Case B)
    entry = next(e for e in manifest if e["iq"].startswith("qpsk_002"))
    sig = load_iq(DATASETS / entry["iq"], DATASETS / f"{Path(entry['iq']).stem}.sigmf-meta", entry["iq"])
    res = run_pipeline(sig, top_k=2)
    deep = []
    for a in res.attempts:
        if a.recovered_bits is None:
            continue
        v = validate_bitstream(a.recovered_bits)
        deep.append({"modulation": a.hypothesis.modulation, "len": len(a.recovered_bits),
                     "validator_score": v.correlation_score, "peak": v.peak_index, "passed": v.passed,
                     "steps": [(s[0], s[1]) for s in a.steps]})
    # also anchor stats for the qpsk_002 recovered stream
    tr = truths["qpsk_002"]
    att = next((a for a in res.attempts if a.hypothesis.modulation == "QPSK"), None)
    if att is not None and att.recovered_bits is not None:
        pk, score = correlate_sync(att.recovered_bits)
        head = att.recovered_bits[:80]
        deep.append({"qpsk_002_align64": {"pk": pk, "score64": score},
                     "head_bits_match_frame": int(np.count_nonzero(head == tr.frame[:len(head)])),
                     "head_len": int(len(head))})
    results["_qpsk_002_deep_dive"] = {"accepted": res.accepted.hypothesis.modulation if res.accepted else None,
                                      "attempts": deep}

    (ROOT / "tools" / "failure_forensics.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    mism = [k for k, r in results.items() if isinstance(r, dict) and r.get("matches_step3") is False]
    print(f"\nCross-check vs Step 3: {'ALL MATCH' if not mism else 'MISMATCH: ' + str(mism)}")
    print("Wrote tools/failure_forensics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
