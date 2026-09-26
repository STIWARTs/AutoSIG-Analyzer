from __future__ import annotations

from datetime import datetime

import streamlit as st

from backend.storage import list_recent, load_analysis


def _pretty_time(timestamp: str) -> str:
    try:
        return datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, TypeError):
        return timestamp


def render() -> None:
    st.markdown("<div class='screen-heading'>AutoSIG Analyzer</div>", unsafe_allow_html=True)
    st.markdown("**Signal analysis and recovery workstation**")
    st.caption("IQ / SigMF and WAV ingestion · DSP characterization · trained I/Q classification · preamble-confirmed recovery acceptance")
    st.markdown("<div class='instrument-panel'><span class='muted'>MVP operating envelope</span><br>"
                "QPSK recovery · block de-interleaving · convolutional/Viterbi FEC · BPSK classification</div>",
                unsafe_allow_html=True)

    active_id = st.session_state.get("active_analysis_id")
    result = st.session_state.get("result")
    if result:
        status = "recovery accepted (preamble detected)" if result.accepted else "no hypothesis passed preamble detection"
        origin = "from history" if active_id is not None else "live"
        st.subheader("Active analysis")
        st.markdown(f"<div class='instrument-panel mono'><span class='muted'>CURRENT</span><br>"
                    f"<strong>{result.analysis.signal.filename}</strong> — {status} "
                    f"<span class='muted'>({origin})</span></div>", unsafe_allow_html=True)
        st.caption("Open Report for the full machine-readable result, or Upload to analyze another capture.")
    else:
        st.caption("Select Upload in the navigation panel to begin.")

    rows = list_recent(10)
    if not rows:
        return
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    st.markdown("#### Recent Analyses")
    header = st.columns((4.2, 3.1, 2.4, 1.4, 1.1))
    for column, label in zip(header, ("FILENAME", "TIMESTAMP (UTC)", "ACCEPTED", "CORR", "")):
        column.markdown(f"<span class='muted' style='font-size:.72rem'>{label}</span>", unsafe_allow_html=True)
    for row in rows:
        is_active = row["id"] == active_id
        marker = "<span style='color:var(--accent)'>● </span>" if is_active else "<span style='color:var(--line)'>○ </span>"
        modulation = row["accepted_modulation"] or "<span class='muted'>no hypothesis accepted</span>"
        correlation = f"{row['correlation_score']:.3f}" if row["correlation_score"] is not None else "—"
        columns = st.columns((4.2, 3.1, 2.4, 1.4, 1.1))
        columns[0].markdown(f"{marker}<span class='mono'>{row['input_filename']}</span>", unsafe_allow_html=True)
        columns[1].markdown(f"<span class='mono muted'>{_pretty_time(row['timestamp'])}</span>", unsafe_allow_html=True)
        columns[2].markdown(modulation, unsafe_allow_html=True)
        columns[3].markdown(f"<span class='mono'>{correlation}</span>", unsafe_allow_html=True)
        if columns[4].button("View", key=f"view_{row['id']}", use_container_width=True):
            st.session_state.result = load_analysis(row["id"])
            st.session_state.active_analysis_id = row["id"]
            st.rerun()
