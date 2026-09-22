# System Architecture

## Guiding Principle

AutoSIG is built as a **presentation layer on top of a signal-processing and ML engine**, deliberately kept separate so the engine can be reused later behind a different frontend (a future React app, or a native desktop app) without being rewritten. For the prototype stage, the presentation layer is Streamlit and the engine is a Python backend; they run in the same process for simplicity, but the backend code must not import anything from the Streamlit layer, so the boundary stays real.

## High-Level Data Flow

```
        .IQ / .WAV file
               │
               ▼
        ┌─────────────┐
        │  Ingestion  │  parse file + metadata into a common complex-sample array
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ DSP Analysis│  FFT/PSD, spectrogram, sample rate, bandwidth, SNR, symbol rate
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Modulation  │  CNN classifier on raw I/Q → per-class confidence
        │Classification│
        └──────┬──────┘
               ▼
        ┌─────────────────┐
        │ Hypothesis Engine│  combine modulation confidence + candidate
        │  (Top-K ranking) │  interleaving/FEC pairs → ranked hypothesis list
        └──────┬──────────┘
               ▼
        ┌─────────────────────────────┐
        │ Recovery Chain (per hypothesis, in rank order) │
        │  Sync → Demodulation → De-interleave → FEC decode │
        └──────┬──────────────────────┘
               ▼
        ┌─────────────────┐
        │Validation & Bitstream│  correlate recovered bits against known
        │   Correlation        │  preamble/header pattern; every ranked
        └──────┬───────────────┘  hypothesis is tested, first PASS is accepted
               ▼
        ┌─────────────┐
        │   Report    │  parameters, chosen hypothesis, recovered bitstream,
        └─────────────┘  header/payload split, correlation score
               │
               ▼
        ┌─────────────┐
        │   Storage   │  persist every completed run (pass or fail) to a
        └─────────────┘  SQLite history (data/autosig.db) for Dashboard replay
```

## Component Responsibilities

- **Ingestion** — reads either file type into one common in-memory representation: a complex NumPy array of samples plus a metadata dictionary (sample rate, center frequency, datatype, source format). See `08-file-formats.md`.
- **DSP Analysis** — pure signal processing, no learned models. Produces the spectrum plot, waterfall plot, and the measurable characteristics (sample rate, bandwidth, estimated SNR, estimated symbol rate). See `02-dsp-pipeline.md`.
- **Modulation Classification** — the one place AI/ML is used for *identification*. Outputs a probability per modulation class, not a hard decision. See `03-modulation-classification.md`.
- **Hypothesis Engine** — turns the classifier's probabilities into a short, ranked list of full configurations (modulation + interleaving + FEC) worth actually attempting recovery on. See `04-hypothesis-engine.md`.
- **Recovery Chain** — deterministic DSP, not ML. For a given hypothesis, actually attempts synchronization, demodulation, de-interleaving, and FEC decoding. See `05-recovery-chain.md`.
- **Validation & Bitstream Correlation** — the safety net. A hypothesis is only accepted if the bits it produced correlate against the expected preamble/header pattern above a threshold. This is what stops an AI misclassification from silently producing garbage output. See `06-validation-correlation.md`.
- **Report** — a human-readable summary of everything above, downloadable from the UI.
- **Storage** — persists every completed analysis (whether a hypothesis validated or all failed) to a standard-library SQLite database at `data/autosig.db`, and reconstructs a stored run back into the same in-memory result the live pipeline returns so the Dashboard can replay any past analysis. This is the only stage with durable state; it adds no external database dependency.

## Why Validation Is a First-Class Component, Not an Afterthought

The core idea that differentiates AutoSIG from "run a classifier and trust it" is that every AI prediction is treated as a hypothesis to be tested, not a fact to be acted on. A wrong modulation guess does not quietly propagate into a wrong bitstream — it fails validation, and the system automatically moves to the next-most-likely hypothesis. This is why the architecture keeps validation as its own explicit stage rather than folding it into recovery.
