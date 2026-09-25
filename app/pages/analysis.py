import plotly.graph_objects as go
import streamlit as st

from app.components.charts import constellation_figure, dark_layout, palette


def render() -> None:
    result = st.session_state.get("result")
    if not result:
        st.warning("Upload and analyze a signal first.")
        return
    analysis = result.analysis
    has_rate = analysis.signal.sample_rate is not None
    st.markdown("<div class='screen-heading'>DSP Analysis</div>", unsafe_allow_html=True)
    left, right = st.columns((3.25, 1))
    with left:
        spectrum = go.Figure(go.Scatter(x=analysis.frequency_hz, y=analysis.psd_db, line=dict(color="#378ADD")))
        spectrum.update_layout(title="Power spectral density",
                               xaxis_title="Frequency (Hz)" if has_rate else "Normalized frequency (cycles/sample)",
                               yaxis_title="dB/Hz" if has_rate else "Relative power (dB)")
        st.plotly_chart(dark_layout(spectrum), key="psd")
        waterfall = go.Figure(go.Heatmap(x=analysis.spectrogram_time_s, y=analysis.spectrogram_frequency_hz,
                                         z=analysis.spectrogram_db, colorscale="Viridis", colorbar=dict(title="dB")))
        waterfall.update_layout(title="Waterfall", xaxis_title="Time (s)" if has_rate else "Sample index (normalized)",
                                yaxis_title="Frequency (Hz)" if has_rate else "Normalized frequency")
        st.plotly_chart(dark_layout(waterfall, 340), key="waterfall")
    with right:
        st.markdown("#### Measured parameters")
        if not has_rate:
            st.warning("Sample rate is unknown. Spectrum and constellation are relative only; bandwidth, symbol rate, "
                       "and center frequency in Hz are unavailable.")
        rows = []
        # Surfaced as a qualifier on the Center Frequency row rather than a raw
        # numeric row: False means the displayed frequency is a baseband offset,
        # not an absolute RF frequency.
        absolute_available = bool(analysis.parameters.get("absolute_frequency_available"))
        for key, value in analysis.parameters.items():
            if key == "absolute_frequency_available":
                continue
            label = key.replace("_", " ").replace("hz", "Hz").replace("db", "dB")
            if key == "center_frequency_hz" and not absolute_available:
                label += " <span class='muted'>(relative to baseband)</span>"
            display = "UNAVAILABLE" if value is None else f"{value:,.2f}"
            state = " unavailable" if value is None else ""
            rows.append(f"<tr><td class='label'>{label}</td><td class='value{state}'>{display}</td></tr>")
        st.markdown("<div class='instrument-panel'><table class='measurement'>" + "".join(rows) + "</table></div>",
                    unsafe_allow_html=True)
        sample = analysis.signal.samples[: min(5000, len(analysis.signal.samples))]
        st.plotly_chart(constellation_figure(sample, "Raw I/Q (pre-synchronization)", size=300),
                        use_container_width=False, key="constellation")
    st.markdown("#### Trained CNN confidence")
    ordered = sorted(result.probabilities.items(), key=lambda item: item[1], reverse=True)
    confidence = go.Figure(go.Bar(x=[score for _, score in ordered], y=[name for name, _ in ordered],
                                  orientation="h", marker_color="#3E92CC", text=[f"{score:.1%}" for _, score in ordered],
                                  textposition="outside", textfont=dict(color=palette()["text"], family="IBM Plex Mono")))
    confidence.update_layout(xaxis=dict(range=[0, 1.12], tickformat=".0%", title="Model confidence"),
                            yaxis=dict(autorange="reversed", title=None), height=190)
    st.plotly_chart(dark_layout(confidence, 190), key="cnn_confidence")
