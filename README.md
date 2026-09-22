# AutoSIG Analyzer

AutoSIG Analyzer is a Streamlit prototype for `.iq`/SigMF and `.wav` signal
analysis. It applies deterministic DSP analysis, a trained raw-I/Q PyTorch CNN,
Top-K modulation hypotheses, and a real recovery chain validated through frame
preamble correlation.

## MVP boundary

The implemented recovery path is deliberately limited to the documented MVP:
QPSK and BPSK demodulation, block de-interleaving, and rate-1/2 convolutional
decoding with Viterbi. The CNN has two trained modulation classes, QPSK and
BPSK, and both are fully demodulated and validated through the recovery chain in
this MVP. Every ranked hypothesis is pushed through the chain (not stopped at
the first pass), so a misclassified candidate is visibly tested and refuted.

## Setup

An isolated Conda environment is already expected at `.conda`. To recreate it:

```powershell
conda create --prefix .conda python=3.14 pip -y
.\.conda\python.exe -m pip install -r requirements.txt
# Optional offline generator runtime when a compatible GNU Radio build exists
conda install --prefix .conda -c conda-forge gnuradio -y
```

GNU Radio is used for offline synthetic capture generation when its Conda
runtime is available. The generator has an explicitly labeled sample-accurate
repeat/rotator/AWGN fallback for Windows/Python combinations that do not yet
ship GNU Radio; it never pretends fallback captures are GNU Radio captures.
Inspect `datasets/manifest.json` to see which generator created each capture.
The running application needs the trained model under `models/` but does not
import GNU Radio.

## Generate, train, and run

```powershell
# Generate GNU Radio QPSK/BPSK captures as .iq + SigMF + stereo .wav
.\.conda\python.exe training/generate_dataset.py --count-per-class 32

# Train the CNN and write models/modulation_cnn.pt plus measured test metrics
.\.conda\python.exe training/train_classifier.py --epochs 18

# Run the application
.\.conda\python.exe -m streamlit run app/streamlit_app.py
```

In the Upload screen, upload an IQ file and its matching SigMF sidecar together;
the app pairs them by filename stem automatically. If an IQ sidecar is absent,
enter the sample rate in the inline metadata form for absolute-Hz analysis, or
continue with clearly labelled relative-only spectral/constellation analysis.
Any generated `datasets/*.wav` file remains a single-file upload.
The app runs the real trained classifier output through its hypothesis list;
recovery is accepted only when the recovered bits pass preamble correlation.
The Analysis screen shows the raw I/Q constellation (pre-synchronization), while
the Bitstream screen additionally shows the recovered-symbol constellation
(post-synchronization) once a hypothesis has been validated.

## Analysis history

Every completed run — whether a hypothesis validated or all candidates failed —
is persisted to a SQLite database at `data/autosig.db` using only the Python
standard library (no external database server, no new dependencies). The
Dashboard lists the most recent analyses and lets you select any one to reload
its full result into the Analysis, Recovery, Bitstream, and Report screens
exactly as it rendered live. Because the history is stored on disk, it survives a
server restart, not just the browser session. Delete the `data/` folder to reset
the history.

## Layout

- `app/`: Streamlit screens and shared UI components.
- `backend/`: ingestion, DSP, ML inference, hypotheses, recovery, validation,
  storage (SQLite analysis history), and report generation. It does not import
  from `app/`.
- `gnuradio/`: offline GNU Radio capture flowgraph.
- `training/`: dataset generator and CNN training script.
- `datasets/`: generated labeled IQ, SigMF, WAV and manifest artifacts.
- `models/`: inference-ready CNN checkpoint and measured metrics.
- `data/`: SQLite analysis-history database (`autosig.db`), created on first run.

## Verification

Run `pytest` after creating data/model; then use the real upload UI for both
the IQ/SigMF pair and the matching WAV. For deployment, follow
`docs/13-deployment-and-demo.md`: push to GitHub and deploy
`app/streamlit_app.py` through Streamlit Community Cloud.
