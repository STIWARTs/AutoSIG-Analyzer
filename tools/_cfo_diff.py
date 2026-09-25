"""Ad-hoc: compare baseline vs after pass/fail per file, focus on regressions."""
import json

b = {r["file"]: r for r in json.load(open("tools/cfo_ab_baseline.json"))["rows"]}
a = {r["file"]: r for r in json.load(open("tools/cfo_ab_after.json"))["rows"]}
print(f"{'file':<34}{'snr':>5} | {'base sync_err':>13} {'b_pass':>6} | "
      f"{'after sync_err':>13} {'a_pass':>6} | after display_err")
regress = []
for f, ra in a.items():
    rb = b[f]
    if ra["snr_db"] != 18.0:
        continue
    bp = rb["iq_pipeline"]["true_validated"]
    ap = ra["iq_pipeline"]["true_validated"]
    if bp != ap:
        regress.append((f, ra["snr_db"], bp, ap))
    def e(r, k):
        v = r["iq"][k]
        return "REFUSED" if v is None else f"{v:.3f}"
    print(f"{f:<34}{ra['snr_db']:>5} | {e(rb,'sync_err'):>13} {str(bp):>6} | "
          f"{e(ra,'sync_err'):>13} {str(ap):>6} | {e(ra,'display_err')} corr {ra['iq_pipeline']['true_corr']}")
print("\nRegressions (was pass, now fail) across WHOLE corpus:")
for f, ra in a.items():
    rb = b[f]
    if rb["iq_pipeline"]["true_validated"] and not ra["iq_pipeline"]["true_validated"]:
        print(f"  IQ  {f:<34} snr {ra['snr_db']:>5}  base_sync_err={rb['iq']['sync_err']:.3f} "
              f"after_sync_err={ra['iq']['sync_err']}")
    if rb["wav_pipeline"]["true_validated"] and not ra["wav_pipeline"]["true_validated"]:
        print(f"  WAV {f:<34} snr {ra['snr_db']:>5}  base_sync_err={rb['wav']['sync_err']:.3f} "
              f"after_sync_err={ra['wav']['sync_err']}")
