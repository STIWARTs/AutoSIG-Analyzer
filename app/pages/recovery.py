import streamlit as st
from app.components.widgets import status_badge


def render() -> None:
    result = st.session_state.get("result")
    if not result:
        st.warning("Upload and analyze a signal first.")
        return
    st.markdown("<div class='screen-heading'>Hypothesis Recovery</div>", unsafe_allow_html=True)
    st.caption("Ranked from the trained classifier's real softmax output; each candidate is recovered in order and "
               "accepted only when its recovered bits contain the known frame preamble above the correlation threshold.")
    # Interleaving and FEC are identical on every candidate (never varied or
    # independently tested), so presenting them per hypothesis would imply a
    # search that does not happen; state the fixed configuration once instead.
    st.markdown("<div class='instrument-panel'><span class='muted'>Fixed recovery configuration (MVP scope)</span><br>"
                "Block interleaving · Convolutional/Viterbi FEC — modulation is the only hypothesized, "
                "varying dimension.</div>", unsafe_allow_html=True)
    for hypothesis in result.hypotheses:
        attempt = next((item for item in result.attempts if item.hypothesis.rank == hypothesis.rank), None)
        dim = " dim" if attempt and (not result.accepted or attempt is not result.accepted) else ""
        content = (f"<div class='hypothesis{dim}'><div class='hypothesis-title'>Hypothesis {hypothesis.rank}"
                   f" <span class='mono'>{hypothesis.score:.1%}</span></div><div class='hypothesis-meta'>"
                   f"{hypothesis.modulation} <span class='muted'>(predicted modulation)</span></div>")
        if attempt:
            for step, status, detail in attempt.steps:
                content += ("<div style='display:flex;justify-content:space-between;align-items:center;"
                            "padding:8px 0;border-bottom:1px solid var(--line)'><span>" + step +
                            f" <span class='muted'>· {detail}</span></span>{status_badge(status)}</div>")
        else:
            content += "<div style='padding:8px 0'>" + status_badge("IN PROGRESS") + "</div>"
        st.markdown(content + "</div>", unsafe_allow_html=True)
    if result.accepted:
        st.success(f"Recovery accepted: Hypothesis #{result.accepted.hypothesis.rank} — the known preamble was detected "
                   "in its recovered bits above the correlation threshold. This evidences synchronization, demodulation "
                   "and framing — it does not prove every payload bit is correct.")
    else:
        st.error("No hypothesis's recovered bits contained the known preamble above the correlation threshold.")
