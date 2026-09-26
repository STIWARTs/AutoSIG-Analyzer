import streamlit as st

from app.components.charts import constellation_figure


def render() -> None:
    result = st.session_state.get("result")
    if not result or not result.validation or not result.validation.passed:
        st.warning("An accepted recovery (known preamble detected in the recovered bits) is required before bitstream display.")
        return
    validation = result.validation
    st.markdown("<div class='screen-heading'>Recovered Bitstream — Preamble Confirmed</div>", unsafe_allow_html=True)
    # The scope disclaimer belongs directly under the headline, not only in the
    # supporting captions, so the title can never be read as "payload proven".
    st.caption("Scope of “confirmed”: the known 32-bit preamble was detected above the correlation threshold. "
               "This does not independently verify every payload bit shown below.")
    st.markdown("<div class='muted'>CORRELATION SCORE</div><div class='correlation-value'>" +
                f"{validation.correlation_score:.3f}</div>", unsafe_allow_html=True)
    st.caption(f"Preamble peak at recovered-bit offset {validation.peak_index}. Header includes preamble and frame header.")
    st.caption("Validation means the known 32-bit preamble correlated above the acceptance threshold; the payload bits "
               "that follow it are displayed as recovered, but validation does not confirm each of them is correct.")
    header = "".join(map(str, validation.header_bits))
    payload = "".join(map(str, validation.payload_bits))
    st.markdown("<div class='bitstream'><div class='bit-header'><span class='muted'>HEADER</span><br>" + header +
                "</div><div class='bit-payload'><span class='muted'>PAYLOAD</span><br>" + payload + "</div></div>",
                unsafe_allow_html=True)
    # The recovered-symbol constellation is only meaningful once a hypothesis has
    # cleared Frame Validation, so it lives behind the same gate as this screen.
    accepted = result.accepted
    symbols = accepted.synchronized_symbols if accepted is not None else None
    if symbols is not None and len(symbols):
        info, plot = st.columns((1.25, 1))
        with info:
            st.markdown("#### Recovered symbol constellation")
            st.caption("Carrier-, timing- and phase-corrected symbols captured at the synchronization "
                       "step, before demodulation collapsed them to bits. Tight clusters confirm a clean "
                       "lock; compare with the diffuse “Raw I/Q (pre-synchronization)” ring on the "
                       "Analysis screen.")
            rows = [("Modulation", accepted.hypothesis.modulation),
                    ("Symbols plotted", f"{len(symbols):,}"),
                    # The resolved carrier phase state from the demodulation step
                    # (QPSK: 0/90/180/270°, BPSK: 0/180°), not the hypothesis rank.
                    ("Phase state", "—" if accepted.phase_state_degrees is None
                     else f"{accepted.phase_state_degrees:.0f}°")]
            table = "".join(f"<tr><td class='label'>{k}</td><td class='value'>{v}</td></tr>" for k, v in rows)
            st.markdown("<div class='instrument-panel'><table class='measurement'>" + table + "</table></div>",
                        unsafe_allow_html=True)
        with plot:
            st.plotly_chart(constellation_figure(symbols, "Recovered Symbols (post-synchronization)", size=420),
                            use_container_width=False, key="recovered_constellation")
