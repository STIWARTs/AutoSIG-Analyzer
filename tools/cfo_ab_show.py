"""Pretty-print a tools/cfo_ab_<tag>.json summary table. Usage: python tools/cfo_ab_show.py baseline"""
import json
import sys

d = json.load(open(f"tools/cfo_ab_{sys.argv[1] if len(sys.argv) > 1 else 'baseline'}.json", encoding="utf-8"))
s = d["summary"]
order = ["-2.0", "0.0", "4.0", "8.0", "12.0", "18.0", "ALL"]


def fmt(v):
    return "   --   " if v is None else f"{v:8.3f} "


print(f"tag={d['tag']}  (errors vs true CFO from manifest, Hz; 'ref' = estimator refusals)")
for kind, key in (("IQ (.iq+.sigmf-meta)", "iq"), ("WAV (.wav)", "wav")):
    print(f"\n--- {kind}: |estimate - truth| Hz ---")
    print(f"{'SNR':>5} {'n':>3} | {'disp med':>9} {'disp max':>9} {'refused':>8} | {'sync med':>9} {'sync max':>9}")
    for level in order:
        e, c = s[level][key + "_display"], s[level][key + "_sync"]
        print(f"{level:>5} {e['n']:>3} | {fmt(e['median_abs_err_hz'])} {fmt(e['max_abs_err_hz'])} "
              f"{e['n_refused_or_missing']:>6}/{e['n']:<2} | {fmt(c['median_abs_err_hz'])} {fmt(c['max_abs_err_hz'])}")
print("\n--- pipeline Frame Validation (full run_pipeline, top_k=2) ---")
print(f"{'SNR':>5} | {'IQ true-mod validated':>22} | {'IQ accepted == true':>19} | {'WAV true-mod validated':>23} | {'WAV accepted == true':>20}")
for level in order:
    ip, wp = s[level]["iq_pipeline"], s[level]["wav_pipeline"]
    print(f"{level:>5} | {ip['true_mod_validated']:>12}/{ip['n']:<8} | {ip['accepted_true_mod']:>9}/{ip['n']:<9} "
          f"| {wp['true_mod_validated']:>13}/{wp['n']:<8} | {wp['accepted_true_mod']:>10}/{wp['n']:<9}")
# Worst offenders for the sync estimator, for the record
worst = sorted((r for r in d["rows"]), key=lambda r: -r["iq"]["sync_err"])[:8]
print("\n--- 8 worst IQ sync errors (baseline evidence) ---")
for r in worst:
    disp = r["iq"]["display_est_hz"]
    print(f"{r['file']:<32} snr={r['snr_db']:>5} truth={r['true_cfo_hz']:>9.2f} "
          f"sync={r['iq']['sync_est_hz']:>9.2f} (err {r['iq']['sync_err']:>7.2f})  "
          f"display={'REFUSED' if disp is None else f'{disp:9.2f}'}")
