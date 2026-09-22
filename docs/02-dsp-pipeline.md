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
- **Center frequency** — from metadata when available, otherwise estimated as the centroid of the occupied spectrum.
- **Estimated SNR** — ratio of in-band signal power to the estimated noise floor power.
- **Estimated symbol rate** — from cyclostationary features (e.g. spectral peaks in the squared or fourth-power spectrum) or from the spacing of transitions in the envelope, depending on modulation family.

### 5. Synchronization

This step is easy to under-scope, and doing so is where blind recovery pipelines usually break in practice — it deserves its own explicit stage rather than being folded silently into demodulation.

- **Carrier frequency offset correction** — a Costas loop (for PSK/QAM) or a frequency discriminator (for FSK) removes residual frequency offset between the recording and the true carrier.
- **Symbol timing recovery** — a timing error detector (e.g. Gardner or Mueller & Müller) locks onto the correct sampling instants for each symbol.

Synchronization runs once per hypothesis in the recovery chain (`05-recovery-chain.md`), since the correct demodulator to lock onto depends on which modulation is being attempted.

## Tools

- `NumPy` / `SciPy` for FFT, filtering, resampling, and spectral estimation.
- `GNU Radio` (via its Python bindings, or simply as the tool used to *generate* the synthetic training/demo data) for anything that benefits from an existing, tested DSP block rather than a hand-rolled implementation.
- `Plotly` or `Matplotlib` for rendering the spectrum, waterfall, and constellation plots inside the Streamlit UI.

## Output of This Stage

A structured object containing: the raw complex samples, the metadata dictionary, the spectrum/waterfall/constellation plot data, and the estimated parameters (sample rate, bandwidth, center frequency, SNR, symbol rate). This object is passed into the modulation classifier next.
