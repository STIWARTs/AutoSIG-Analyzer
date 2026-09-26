# DSP Pipeline: Ingestion Through Characterization

## Purpose

Before any AI/ML runs, the raw recording is turned into measurable, deterministic characteristics. This stage answers "what does the physical signal look like" — it never guesses at content, only measures shape.

## Steps

### 1. Ingestion

The parsed file (see `08-file-formats.md`) becomes a complex-valued NumPy array `x[n]` plus a metadata dictionary containing at least `sample_rate` and, where known, `center_frequency` and `datatype`.

### 2. Preprocessing

- Optional DC offset removal.
- Optional low-pass/band-pass filtering to isolate the signal of interest if the recording contains more bandwidth than the signal occupies.
- Optional resampling to a standard rate the downstream classifier expects.

### 3. Spectral Analysis

- **FFT / Power Spectral Density (PSD)** — computed with `scipy.signal.welch` or an FFT-based estimator, used to render the spectrum plot and to estimate occupied bandwidth.
- **Spectrogram / Waterfall** — a time-frequency view (`scipy.signal.stft` or `matplotlib.mlab.specgram`), showing how the signal's spectral content changes over time. This is one of the required visualizations from the PS.
- **Constellation plot** — for a complex baseband signal, plotting I vs Q gives a quick visual sanity check of modulation order before the classifier runs, and is a nice-to-have visualization for the UI.

### 4. Parameter Estimation

From the spectral analysis, estimate:

- **Sample rate** — read from file metadata (SigMF sidecar for `.IQ`, WAV header for `.wav`); cross-checked against the Nyquist bandwidth of the observed spectrum.
- **Occupied bandwidth** — the width of the main spectral lobe above a noise-floor threshold.
- **Center frequency** — the measured carrier offset (see Synchronization below) anchored to the metadata center frequency when the capture provides one. Synthetic baseband files store a `0.0` placeholder, which is not an RF anchor: the `absolute_frequency_available` parameter is true only when a genuine nonzero center frequency is known (SigMF metadata or manual entry), and the UI qualifies the value as “relative to baseband” otherwise.
- **Estimated SNR** — ratio of in-band signal power to the estimated noise floor power.
- **Estimated symbol rate** — from cyclostationary features (e.g. spectral peaks in the squared or fourth-power spectrum) or from the spacing of transitions in the envelope, depending on modulation family.

### 5. Synchronization

This step is easy to under-scope, and doing so is where blind recovery pipelines usually break in practice — it deserves its own explicit stage rather than being folded silently into demodulation.

- **Carrier frequency offset estimation — one shared, quality-gated estimator.** A single implementation (`estimate_carrier_offset` in `backend/dsp/carrier.py`) serves both the DSP display path above and the Recovery Chain's carrier correction (`backend/dsp/sync.py::synchronize_psk`), so the number shown on the Analysis screen and the number actually used to correct the signal can never diverge. It searches the zero-padded periodogram of the squared (BPSK) or fourth-power (QPSK) signal, refines the peak by parabolic interpolation, and applies a concentration gate: a peak below ~4× the band mean is indistinguishable from the noise floor, so the estimate is **refused (returned as `None`) rather than reported as a lie** — and `None` (“no reliable estimate”) is never coerced to a numeric 0 Hz anywhere downstream. On refusal, synchronization reports NO LOCK / LOW CONFIDENCE and recovery proceeds without frequency correction, leaving frame validation as the final evidence gate.
- **Symbol timing recovery** — the sampling instant that maximizes constellation concentration at the assumed symbol rate.
- **Phase ambiguity** is deliberately *not* resolved here: the higher-order-power phase is quadrant-ambiguous, so the Recovery Chain resolves it with its own discrete candidate-rotation search at demodulation (`05-recovery-chain.md`). The constant-phase (polyfit-intercept) term is measured and preserved for diagnostics but not applied to samples — applying it empirically lands near the ±45° QPSK decision boundary and corrupts demodulation (see the flag documentation in `backend/dsp/sync.py`).

Synchronization runs once per hypothesis in the recovery chain (`05-recovery-chain.md`), since the correct demodulator to lock onto depends on which modulation is being attempted.

**Baseline and A/B tooling:** the estimator's accuracy is validated corpus-wide against manifest ground truth (`tools/cfo_ab_report.py`, run as `--tag baseline|after`; the post-refactor run `tools/cfo_ab_after.json` is the current reference baseline: median |error| ≈ 0.09 Hz, corpus Frame-Validation pass 42/64 IQ and 44/64 WAV). The superseded unwrap+polyfit estimator is preserved disabled behind `USE_LEGACY_POLYFIT_CFO` for A/B comparison.

## Tools

- `NumPy` / `SciPy` for FFT, filtering, resampling, and spectral estimation.
- `GNU Radio` (via its Python bindings, or as the *intended* offline tool to generate the synthetic training/demo data — the shipped corpus was actually produced by the generator's labeled, flowgraph-equivalent NumPy fallback; see `07-data-generation.md`) for anything that benefits from an existing, tested DSP block rather than a hand-rolled implementation.
- `Plotly` or `Matplotlib` for rendering the spectrum, waterfall, and constellation plots inside the Streamlit UI.

## Output of This Stage

A structured object containing: the raw complex samples, the metadata dictionary, the spectrum/waterfall/constellation plot data, and the estimated parameters (sample rate, bandwidth, center frequency, SNR, symbol rate). This object is passed into the modulation classifier next.
