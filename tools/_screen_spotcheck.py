"""Spot-check: no exceptions on any screen for 5 representative files (post-refactor default)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest
from backend.ingestion.parser import load_iq, load_wav
from backend.pipeline import run_pipeline

CASES = [
    ("QPSK high-SNR (was regressed)", "qpsk_023_snr+18_cfo+75", "iq"),
    ("BPSK high-SNR", "bpsk_011_snr+18_cfo+79", "iq"),
    ("WAV", "bpsk_005_snr+18_cfo+50", "wav"),
    ("Low-SNR / NO-LOCK (WARN path)", "qpsk_000_snr-2_cfo-74", "iq"),
    ("BPSK low-SNR", "bpsk_000_snr-2_cfo-78", "iq"),
]
PAGES = ("Dashboard", "Upload", "Analysis", "Recovery", "Bitstream", "Report")

for name, stem, kind in CASES:
    if kind == "iq":
        sig = load_iq(f"datasets/{stem}.iq", f"datasets/{stem}.sigmf-meta", filename=f"{stem}.iq")
    else:
        sig = load_wav(Path(f"datasets/{stem}.wav"), filename=f"{stem}.wav")
    res = run_pipeline(sig)
    sync_locked = [a for a in res.attempts]
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=60)
    at.session_state["result"] = res
    at.run()
    bad = []
    for page in PAGES:
        at.sidebar.radio[0].set_value(page)
        at.run()
        if len(at.exception) or len(at.error):
            bad.append((page, [str(e.value) for e in at.exception]))
    warn = any(s == "WARN" for a in res.attempts for _, s, _ in a.steps)
    accepted = res.accepted.hypothesis.modulation if res.accepted else None
    print(f"{name:<32} accepted={str(accepted):<6} warn_step={warn} "
          f"screens_exceptions={sum(len(e) for _, e in bad)}")
    for page, excs in bad:
        print(f"    !! {page}: {excs}")
print("SPOT CHECK DONE")
