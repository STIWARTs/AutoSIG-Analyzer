from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from app.components.widgets import apply_theme
from app.pages import analysis, bitstream, dashboard, recovery, report
from backend.ingestion.parser import parse_upload
from backend.pipeline import run_pipeline
from backend.storage import save_analysis

st.set_page_config(page_title="AutoSIG Analyzer", layout="wide")
apply_theme()


def _capture_stem(filename: str) -> str:
    """Return the matching stem for signal.iq and signal.sigmf-meta."""
    lower = filename.lower()
    if lower.endswith(".sigmf-meta"):
        return filename[:-len(".sigmf-meta")]
    return Path(filename).stem


def upload_screen() -> None:
    st.markdown("<div class='screen-heading'>Upload Signal</div>", unsafe_allow_html=True)
    st.write("Upload one or more `.iq`, `.sigmf-meta`, or `.wav` files. Matching IQ/SigMF names pair automatically.")
    # Streamlit's file picker validates extensions against a strict allowlist that
    # rejects the hyphenated ".sigmf-meta" sidecar, so we accept every file type and
    # classify by suffix below (only .iq/.wav are treated as captures; unmatched
    # files are ignored). This keeps automatic IQ/SigMF pairing reachable.
    uploaded = st.file_uploader("Signal files", type=None,
                                accept_multiple_files=True, key="uploads")
    signals = [item for item in uploaded if item.name.lower().endswith((".iq", ".wav"))]
    sidecars = {_capture_stem(item.name): item for item in uploaded if item.name.lower().endswith(".sigmf-meta")}
    signal_file = None
    sigmf_file = None
    if signals:
        signal_file = st.selectbox("Capture to analyze", signals, format_func=lambda item: item.name)
        stem = _capture_stem(signal_file.name)
        sigmf_file = sidecars.get(stem)
        st.write(f"**Selected:** {signal_file.name} ({signal_file.size:,} bytes)")
        if signal_file.name.lower().endswith(".wav"):
            st.caption("WAV header supplies its sample rate; stereo WAV is interpreted as I/Q.")
        elif sigmf_file:
            st.success(f"Automatically paired metadata: {sigmf_file.name}")
        else:
            st.info("No matching SigMF sidecar was uploaded. You can supply capture metadata below, or continue with relative-only analysis.")

    manual_rate: float | None = None
    manual_datatype = "cf32_le"
    manual_center: float | None = None
    if signal_file and signal_file.name.lower().endswith(".iq") and sigmf_file is None:
        with st.form("manual_iq_metadata", border=False):
            st.caption("Optional manual IQ metadata")
            rate_text = st.text_input("Sample rate (Hz)", placeholder="e.g. 48000")
            manual_datatype = st.text_input("Datatype", value="cf32_le", help="Supported: cf32_le or ci16_le")
            center_text = st.text_input("Center frequency (Hz, optional)", placeholder="e.g. 433920000")
            st.form_submit_button("Use supplied metadata")
        try:
            manual_rate = float(rate_text) if rate_text.strip() else None
            manual_center = float(center_text) if center_text.strip() else None
            if manual_rate is not None and manual_rate <= 0:
                raise ValueError
        except ValueError:
            st.error("Sample rate and center frequency must be positive numeric values when provided.")
            manual_rate = None
            manual_center = None

    if st.button("Analyze Signal", type="primary", disabled=signal_file is None):
        try:
            with st.spinner("Running DSP, trained CNN classification, recovery and correlation…"):
                ingested = parse_upload(signal_file, sigmf_file, manual_rate, manual_datatype, manual_center)
                st.session_state.result = run_pipeline(ingested)
                # Persist every completed run (preamble-confirmed or all-failed) and mark it active
                # so the Dashboard highlights it and history survives a server restart.
                st.session_state.active_analysis_id = save_analysis(st.session_state.result)
                st.session_state.pop("select_analysis", None)
            st.success("Analysis complete. Visit Analysis, Recovery, Bitstream, or Report.")
        except Exception as exc:
            st.error(str(exc))


pages = {"Dashboard": dashboard.render, "Upload": upload_screen, "Analysis": analysis.render,
         "Recovery": recovery.render, "Bitstream": bitstream.render, "Report": report.render}
with st.sidebar:
    st.markdown("## AutoSIG")
    selected = st.radio("Navigation", list(pages), label_visibility="collapsed")
pages[selected]()
