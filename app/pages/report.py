import streamlit as st
from backend.reports.generator import build_report


def render() -> None:
    result = st.session_state.get("result")
    if not result:
        st.warning("Upload and analyze a signal first.")
        return
    st.markdown("<div class='screen-heading'>Analysis Report</div>", unsafe_allow_html=True)
    report = build_report(result)
    st.download_button("Download JSON report", report, "autosig_report.json", "application/json", type="primary")
    st.code(report, language="json")
