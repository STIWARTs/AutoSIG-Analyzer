# AutoSIG Analyzer — Instrument Panel Design System

AutoSIG is a signal-analysis instrument, not a SaaS dashboard. Its visual model is an SDR receiver: dense but readable measurement surfaces, quiet dark chrome, and visual priority for spectrum, waterfall, constellation, and recovery evidence.

## Tokens

- **Background:** `#0B0F14`; **panel/surface:** `#12161C`; **hairline divider:** `#232A33`.
- **Accent:** `#3E92CC`, reserved for active navigation, primary controls, selected states, and measured/correlation emphasis.
- **Primary text:** `#E6EDF3`; **secondary text:** `#93A1B0`.
- **Status only:** PASS `#34C759`, FAIL `#FF453A`, IN-PROGRESS `#FFB020`. These colors never decorate unrelated controls, headers, or charts.

There are no gradients, shadows, or card-kit styling. All surfaces use a 1px divider and a maximum `2px` radius.

## Type and layout

IBM Plex Sans is used for headings, labels, navigation, controls, and prose. IBM Plex Mono is used for calculated values, including sample rate, bandwidth, SNR, symbol rate, correlation, and bitstreams. Numeric values use tabular figures and align right in measurement tables.

Every screen begins with a plain heading and a hairline divider; no colored header banners. The sidebar is dark, with active navigation indicated by an accent left rule and accent text rather than a filled pill. On wide screens, Analysis gives most width to plots and retains a compact measurement table in the narrower column.

## Components

- **Measurement table:** labels left; right-aligned monospace values right; 1px row dividers; unavailable values read `UNAVAILABLE`.
- **Hypothesis panel:** hairline top divider; compact metadata; step names/details left and status badge right. Failed attempts dim but remain visible.
- **Status badge:** maximum 2px radius and status color only for actual PASS, FAIL, or IN-PROGRESS state.
- **Plots:** match application background and own the visual field. Waterfalls use `Viridis` or `Magma`, never `Jet`.
- **Bitstream:** correlation is the visual focal point in large accent monospace. Header and payload remain contiguous but use light accent and neutral tints respectively.
- **Alerts and code:** native Streamlit alerts (`st.info`/`st.success`/`st.warning`/`st.error`) and code blocks are flattened to the surface color with a 1px hairline border and a 2px accent left rule — no filled colored banners, no rounded corners, no drop shadow. Status color is still reserved for the PASS/FAIL/IN-PROGRESS badges only.
- **Ingestion:** the file picker accepts all file types because Streamlit's client-side extension validator rejects the hyphenated `.sigmf-meta` sidecar; capture/sidecar classification is done in the backend by filename suffix, preserving automatic IQ/SigMF pairing and the manual-metadata fallback.
