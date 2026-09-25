"""Corpus-wide CFO estimator A/B measurement (baseline vs after recovery-sync refactor).

For every dataset entry (IQ + SigMF pair and its WAV counterpart) this records:
  (a) the true CFO from the manifest (ground truth),
  (b) backend/dsp/analysis.py::_estimate_carrier_offset (display-path estimate, Hz),
  (c) backend/dsp/sync.py::synchronize_psk CFO, converted Hz = rad/sample * fs / 2pi,
plus the full-pipeline Frame Validation outcome (accepted hypothesis + whether the
true-modulation attempt validated). Results are aggregated as median/max absolute
error against (a), split by SNR, and written to tools/cfo_ab_<tag>.json so the
before/after runs are directly comparable.

Usage:  python tools/cfo_ab_report.py --tag baseline|after [--no-pipeline]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.dsp.analysis import _estimate_carrier_offset, prepare_samples  # noqa: E402
from backend.dsp.sync import synchronize_psk  # noqa: E402
from backend.ingestion.parser import load_iq, load_wav  # noqa: E402
from backend.pipeline import run_pipeline  # noqa: E402

DATASETS = ROOT / "datasets"
SAMPLES_PER_SYMBOL = 8  # matches backend.recovery.chain.run_recovery default


def measure_signal(signal, truth_hz: float, label: str) -> dict:
    x = prepare_samples(signal)
    fs = signal.sample_rate
    display_hz = _estimate_carrier_offset(x, fs, label)
    _, sync = synchronize_psk(x, SAMPLES_PER_SYMBOL, label, sample_rate=fs)
    sync_rad = sync["cfo_rad_per_sample"]
    sync_hz = None if sync_rad is None else sync_rad * fs / (2 * np.pi)
    # Agreement between the display path and the (now-shared) recovery path.
    if display_hz is None or sync_hz is None:
        agree = None if (display_hz is None) != (sync_hz is None) else 0.0
    else:
        agree = abs(display_hz - sync_hz)
    return {"display_est_hz": display_hz, "sync_est_hz": sync_hz, "locked": bool(sync["locked"]),
            "display_sync_agree_hz": agree,
            "display_err": None if display_hz is None else abs(display_hz - truth_hz),
            "sync_err": None if sync_hz is None else abs(sync_hz - truth_hz)}


def measure_pipeline(signal, label: str) -> dict:
    result = run_pipeline(signal, top_k=2)
    accepted = result.accepted.hypothesis.modulation if result.accepted else None
    true_validated = False
    true_corr = None
    for attempt in result.attempts:
        if attempt.hypothesis.modulation != label:
            continue
        for step, status, detail in attempt.steps:
            if step == "Frame Validation":
                true_validated = status == "PASS"
                true_corr = float(detail.split()[-1])
    return {"accepted": accepted, "true_validated": true_validated, "true_corr": true_corr,
            "abs_freq_flag": result.analysis.parameters["absolute_frequency_available"]}


def spread(values: list[float | None]) -> dict:
    finite = [v for v in values if v is not None]
    return {"n": len(values), "n_refused_or_missing": len(values) - len(finite),
            "median_abs_err_hz": round(statistics.median(finite), 4) if finite else None,
            "max_abs_err_hz": round(max(finite), 4) if finite else None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--no-pipeline", action="store_true")
    args = parser.parse_args()

    manifest = json.loads((DATASETS / "manifest.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    for index, entry in enumerate(manifest, 1):
        truth, label, snr = entry["frequency_offset_hz"], entry["label"], entry["snr_db"]
        iq_path = DATASETS / entry["iq"]
        meta_path = DATASETS / entry["iq"].replace(".iq", ".sigmf-meta")
        wav_path = DATASETS / entry["wav"]
        cases: dict[str, dict] = {}
        iq_signal = load_iq(iq_path, meta_path if meta_path.exists() else None, filename=entry["iq"])
        cases["iq"] = measure_signal(iq_signal, truth, label)
        if wav_path.exists():
            wav_signal = load_wav(wav_path, filename=entry["wav"])
            cases["wav"] = measure_signal(wav_signal, truth, label)
        if not args.no_pipeline:
            cases["iq_pipeline"] = measure_pipeline(iq_signal, label)
            if wav_path.exists():
                cases["wav_pipeline"] = measure_pipeline(wav_signal, label)
        rows.append({"file": entry["iq"], "label": label, "snr_db": snr, "true_cfo_hz": truth, **cases})
        print(f"[{index:3d}/{len(manifest)}] {entry['iq']}", flush=True)

    snr_levels = sorted({row["snr_db"] for row in rows})
    summary: dict[str, dict] = {}
    for level in snr_levels + ["ALL"]:
        subset = rows if level == "ALL" else [r for r in rows if r["snr_db"] == level]
        summary[str(level)] = {
            "iq_display": spread([r["iq"]["display_err"] for r in subset]),
            "iq_sync": spread([r["iq"]["sync_err"] for r in subset]),
            "wav_display": spread([r["wav"]["display_err"] for r in subset if "wav" in r]),
            "wav_sync": spread([r["wav"]["sync_err"] for r in subset if "wav" in r]),
            "iq_display_sync_agree": spread([r["iq"]["display_sync_agree_hz"] for r in subset]),
            "iq_no_lock": sum(1 for r in subset if not r["iq"]["locked"]),
        }
        if not args.no_pipeline:
            accepted = sum(1 for r in subset if r["iq_pipeline"]["accepted"] == r["label"])
            validated = sum(1 for r in subset if r["iq_pipeline"]["true_validated"])
            summary[str(level)]["iq_pipeline"] = {
                "n": len(subset), "accepted_true_mod": accepted, "true_mod_validated": validated}
            wav_subset = [r for r in subset if "wav_pipeline" in r]
            summary[str(level)]["wav_pipeline"] = {
                "n": len(wav_subset),
                "accepted_true_mod": sum(1 for r in wav_subset if r["wav_pipeline"]["accepted"] == r["label"]),
                "true_mod_validated": sum(1 for r in wav_subset if r["wav_pipeline"]["true_validated"])}
    out = {"tag": args.tag, "rows": rows, "summary": summary}
    out_path = ROOT / "tools" / f"cfo_ab_{args.tag}.json"
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(f"\n===== {args.tag}: |estimate - truth| Hz, split by SNR =====")
    header = f"{'SNR':>5} {'cases':>6} | {'IQ disp med':>11} {'max':>9} ref | {'IQ sync med':>11} {'max':>9} | " \
             f"{'WAV disp med':>12} {'max':>9} ref | {'WAV sync med':>12} {'max':>9}"
    print(header)
    for level, stats in summary.items():
        iq, iq_s = stats["iq_display"], stats["iq_sync"]
        wv, wv_s = stats["wav_display"], stats["wav_sync"]
        fmt = lambda s: (f"{s['median_abs_err_hz']:>11.3f} {s['max_abs_err_hz']:>9.3f}"
                         if s["median_abs_err_hz"] is not None else f"{'—':>11} {'—':>9}")
        print(f"{level:>5} {iq['n']:>6} | {fmt(iq)} {iq['n_refused_or_missing']:>4} | {fmt(iq_s)} | "
              f"{fmt(wv)} {wv['n_refused_or_missing']:>4} | {fmt(wv_s)}")
    if not args.no_pipeline:
        print("\n===== pipeline Frame Validation (true-modulation hypothesis) =====")
        for level, stats in summary.items():
            iq_p, wav_p = stats["iq_pipeline"], stats["wav_pipeline"]
            print(f"{level:>5} | IQ validated {iq_p['true_mod_validated']:>3}/{iq_p['n']:<3} "
                  f"accepted-true {iq_p['accepted_true_mod']:>3}/{iq_p['n']:<3} | "
                  f"WAV validated {wav_p['true_mod_validated']:>3}/{wav_p['n']:<3} "
                  f"accepted-true {wav_p['accepted_true_mod']:>3}/{wav_p['n']}")
    agree = summary["ALL"].get("iq_display_sync_agree")
    if agree:
        print(f"\nIQ display<->recovery agreement (ALL): med {agree['median_abs_err_hz']}, "
              f"max {agree['max_abs_err_hz']}, n {agree['n']}, no-lock {summary['ALL']['iq_no_lock']}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
