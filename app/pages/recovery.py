import streamlit as st
from app.components.widgets import status_badge


def render() -> None:
    result = st.session_state.get("result")
    if not result:
        st.warning("Upload and analyze a signal first.")
        return
    st.markdown("<div class='screen-heading'>Hypothesis Recovery</div>", unsafe_allow_html=True)
    st.caption("Ranked from the trained classifier's real softmax output; each candidate is recovered and validated in order.")
    for hypothesis in result.hypotheses:
        attempt = next((item for item in result.attempts if item.hypothesis.rank == hypothesis.rank), None)
        dim = " dim" if attempt and (not result.accepted or attempt is not result.accepted) else ""
        content = (f"<div class='hypothesis{dim}'><div class='hypothesis-title'>Hypothesis {hypothesis.rank}"
                   f" <span class='mono'>{hypothesis.score:.1%}</span></div><div class='hypothesis-meta'>"
                   f"{hypothesis.modulation} · {hypothesis.interleaving} interleaving · {hypothesis.fec}</div>")
        if attempt:
            for step, status, detail in attempt.steps:
                content += ("<div style='display:flex;justify-content:space-between;align-items:center;"
                            "padding:8px 0;border-bottom:1px solid #232A33'><span>" + step +
                            f" <span class='muted'>· {detail}</span></span>{status_badge(status)}</div>")
        else:
            content += "<div style='padding:8px 0'>" + status_badge("IN PROGRESS") + "</div>"
        st.markdown(content + "</div>", unsafe_allow_html=True)
    if result.accepted:
        st.success(f"Validated recovery: Hypothesis #{result.accepted.hypothesis.rank}")
    else:
        st.error("No hypothesis cleared frame validation.")
