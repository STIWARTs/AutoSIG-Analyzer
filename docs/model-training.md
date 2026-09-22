# How the Modulation Classifier Is Trained

This document records exactly how the CNN behind AutoSIG's modulation
identification is trained, so any reader (judge, reviewer, or future
contributor) can understand and reproduce the model's data provenance without
digging through the code.

## TL;DR

The classifier is trained **entirely on synthetic, computer-generated IQ
captures — not real over-the-air recordings.** Signals are produced by
`training/generate_dataset.py` through `gnuradio/synthetic_flowgraph.py`, with
known ground-truth labels (modulation, interleaving, FEC, SNR, frequency
offset), then consumed by `training/train_classifier.py`. The model only ever
learns the two MVP classes — **BPSK and QPSK** (`CLASS_NAMES = ("BPSK", "QPSK")`).

## Data source: GNU Radio, with a labeled NumPy fallback

- **GNU Radio** performs symbol expansion → frequency-offset rotator → AWGN
  channel → complex file sink whenever a compatible build is installed.
- When GNU Radio is unavailable (common on Windows / Python 3.14), the generator
  falls back to a **sample-accurate NumPy** repeat → rotator → AWGN path.
- `datasets/manifest.json` records which generator produced each capture, and a
  fallback capture is **never** mislabeled as a GNU Radio one.

Rationale for synthetic data is covered in `07-data-generation.md`: controlling
ground truth is the only way to *prove* the pipeline is correct within a
hackathon timeline.

## How each labeled capture is produced

Per capture (default **32 per class = 64 files**):

1. Random **128-bit** payload → `make_frame` (embeds the known preamble/sync
   word used later for correlation validation) → rate-½ **convolutional encode**
   (terminated) → **12-row block interleave**.
2. Mapped to **QPSK** or **BPSK** symbols.
3. Impaired with a random carrier frequency offset (**±85 Hz**) and an SNR drawn
   from the cycling set **{−2, 0, 4, 8, 12, 18} dB**, at **48 kHz** sample rate,
   **8 samples per symbol**.
4. Saved in both PS-required formats: **`.iq`** (+ `.sigmf-meta` sidecar carrying
   the ground-truth label) and a stereo **`.wav`** (I on left, Q on right).

## How the data is fed to the CNN

- Reads `datasets/manifest.json`, shuffles deterministically, splits
  **80% train / 20% test**.
- Each file contributes **12 windows of 256 complex samples**
  (`WINDOW_SIZE = 256`); each window is power-normalized to unit average power
  and represented as a 2×N array (I channel, Q channel).
- Model: a small `ModulationCNN` (a few conv layers → fully connected → softmax).
- Optimizer: **Adam** (lr `1e-3`, weight decay `1e-4`), loss **CrossEntropy**,
  default **18 epochs**.

## Measured result

`models/modulation_cnn.metrics.json` reports a **held-out window accuracy of
≈ 97.44%** over 156 test windows. The trained checkpoint
`models/modulation_cnn.pt` also stores the class list, window size, held-out
accuracy, and file/window counts for traceability.

## Reproduce end to end

```powershell
# 1. Generate the labeled synthetic dataset into datasets/ (+ manifest.json)
.\.conda\python.exe training/generate_dataset.py --count-per-class 32

# 2. Train the CNN and write models/modulation_cnn.pt + measured metrics
.\.conda\python.exe training/train_classifier.py --epochs 18
```

## Important caveat

Because the training data is synthetic, the classifier's robustness is bounded
by how closely the generator's impairment model matches real captures. This is
precisely why the application **never trusts the CNN directly**: every predicted
modulation is treated as a hypothesis and only accepted after it passes real DSP
recovery and bitstream-correlation validation (see `01-architecture.md`,
`05-recovery-chain.md`, and `06-validation-correlation.md`).
