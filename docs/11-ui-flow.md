# UI Flow (Streamlit Screens)

See `design.md` for the visual design system (colors, typography, component styling) these screens should follow.

## 1. Dashboard

Landing screen. Shows the AutoSIG name/branding, a short one-line description, and a link/button into the Upload screen. Below the operating-envelope panel it lists a **Recent Analyses** section backed by the persistent SQLite history (`backend/storage/`): one compact row per stored run showing filename, UTC timestamp, accepted modulation (or "no hypothesis validated"), and correlation score. Each row is selectable — choosing one reloads that run's full result into the session so the Analysis, Recovery, Bitstream, and Report screens render it exactly as it did live, and the active run is marked. The section is omitted entirely when no analyses exist yet.

## 2. Upload

- File uploader accepting `.iq` (with an accompanying `.sigmf-meta` file) or `.wav`.
- Once a file is selected, show basic file info immediately (filename, detected format, sample rate if known) before the user clicks "Analyze Signal."
- An "Analyze Signal" button triggers the pipeline.

## 3. Analysis

Displays the output of the DSP pipeline (`02-dsp-pipeline.md`):

- Spectrum (PSD) plot.
- Waterfall (spectrogram) plot.
- Constellation plot, labelled **Raw I/Q (pre-synchronization)** — the diffuse ring of uncorrected samples, shown before carrier/timing/phase recovery.
- A parameter card: sample rate, bandwidth, center frequency, estimated SNR, estimated symbol rate.
- The modulation classifier's confidence scores (`03-modulation-classification.md`), shown as a simple bar or ranked list.

## 4. Recovery

Displays the Hypothesis Engine's ranked list (`04-hypothesis-engine.md`) and, as each is attempted, the live status of its Recovery Chain steps (`05-recovery-chain.md`):

```
Hypothesis #1 — QPSK + Block + Viterbi
  Synchronization        PASS
  QPSK Demodulation       PASS
  Block De-interleaving   PASS
  Viterbi FEC             PASS
  Frame Validation         FAIL
  → trying next hypothesis...

Hypothesis #2 — QPSK + Diagonal + Viterbi
  ...
  Frame Validation         PASS
  ✓ Validated Recovery
```

This screen is the emotional core of the demo — it should visibly show the fail-then-pass sequence rather than just a final result.

## 5. Bitstream

Shows the accepted hypothesis's recovered bitstream, with the header and payload segments visually distinguished (e.g. different background colors), and the correlation score that justified the split (`06-validation-correlation.md`). It also renders a **Recovered Symbols (post-synchronization)** constellation — the carrier-, timing-, and phase-corrected symbol cloud captured at the synchronization step (tight clusters confirm a clean lock), contrasting with the raw pre-synchronization ring on the Analysis screen. This plot only appears once a hypothesis has cleared frame validation.

## 6. Report

A summary screen combining everything above — detected parameters, the winning hypothesis, the correlation score, and the recovered bitstream — with a download button (e.g. as a text or JSON report file).
