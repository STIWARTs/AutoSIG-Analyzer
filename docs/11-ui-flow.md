# UI Flow (Streamlit Screens)

See `design.md` for the visual design system (colors, typography, component styling) these screens should follow.

## 1. Dashboard

Landing screen. Shows the AutoSIG name/branding, a short one-line description, and a link/button into the Upload screen. Below the operating-envelope panel it lists a **Recent Analyses** section backed by the persistent SQLite history (`backend/storage/`): one compact row per stored run showing filename, UTC timestamp, accepted modulation (or "no hypothesis accepted"), and correlation score. Each row is selectable — choosing one reloads that run's full result into the session so the Analysis, Recovery, Bitstream, and Report screens render it exactly as it did live, and the active run is marked. The section is omitted entirely when no analyses exist yet.

## 2. Upload

- File uploader accepting `.iq` (with an accompanying `.sigmf-meta` file) or `.wav`.
- Once a file is selected, show basic file info immediately (filename, detected format, sample rate if known) before the user clicks "Analyze Signal."
- An "Analyze Signal" button triggers the pipeline.

## 3. Analysis

Displays the output of the DSP pipeline (`02-dsp-pipeline.md`):

- Spectrum (PSD) plot.
- Waterfall (spectrogram) plot.
- Constellation plot, labelled **Raw I/Q (pre-synchronization)** — the diffuse ring of uncorrected samples, shown before carrier/timing/phase recovery.
- A parameter card: sample rate, bandwidth, center frequency (qualified “(relative to baseband)” when no genuine nonzero RF anchor is known — see `02-dsp-pipeline.md`), estimated SNR, estimated symbol rate. The displayed carrier offset is the exact value the Recovery Chain corrects against (one shared estimator).
- The modulation classifier's confidence scores (`03-modulation-classification.md`), shown as a simple bar or ranked list.

## 4. Recovery

Displays the Hypothesis Engine's ranked list (`04-hypothesis-engine.md`) and, as each is attempted, the live status of its Recovery Chain steps (`05-recovery-chain.md`). Modulation is the only hypothesized dimension; interleaving/FEC appear once per screen as a "fixed recovery configuration (MVP scope)" note:

```
Fixed recovery configuration: Block interleaving · Convolutional/Viterbi FEC (MVP scope)

Hypothesis #1 — QPSK (predicted modulation)
  Synchronization        PASS     CFO 0.00689 rad/sample
  QPSK Demodulation       PASS
  Block De-interleaving   PASS
  Viterbi FEC             PASS
  Frame Validation         FAIL
  → trying next hypothesis...

Hypothesis #2 — BPSK (predicted modulation)
  ...
  Frame Validation         PASS
  ✓ Recovery accepted — the known preamble was detected in the recovered bits
    above the correlation threshold (this does not prove every payload bit)
```

When the shared CFO estimator refuses to lock on a too-weak signal, the Synchronization step shows `WARN — NO LOCK` and the attempt continues without frequency correction (never a silent 0 Hz), so Frame Validation remains the judge (`05-recovery-chain.md`).

This screen is the emotional core of the demo — it should visibly show the fail-then-pass sequence rather than just a final result.

## 5. Bitstream

Shows the accepted hypothesis's recovered bitstream, with the header and payload segments visually distinguished (e.g. different background colors), and the correlation score that justified the split (`06-validation-correlation.md`). The screen states explicitly that validation means the known 32-bit preamble was detected above the correlation threshold — it does not confirm that every payload bit shown is correct. It also renders a **Recovered Symbols (post-synchronization)** constellation — the carrier-, timing-, and phase-corrected symbol cloud captured at the synchronization step (tight clusters indicate a clean lock), contrasting with the raw pre-synchronization ring on the Analysis screen. This plot only appears once a hypothesis has been accepted (passed preamble detection).

## 6. Report

A summary screen combining everything above — detected parameters, the winning hypothesis, the correlation score, and the recovered bitstream — with a download button (e.g. as a text or JSON report file).
