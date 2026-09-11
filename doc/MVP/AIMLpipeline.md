#  AI/ML Pipeline

## 6.1 Why ML is used

Some signal classifications are difficult to express reliably with hand-written thresholds.

ML can learn patterns in:

- constellation geometry
- spectral characteristics
- temporal statistics
- phase/frequency behavior
- higher-order statistics
- cyclostationary features

## 6.2 Training-data problem

Real unknown recordings generally do not provide labels such as:

```text
modulation = QPSK
FEC = convolutional
interleaving = block
```

Therefore the initial supervised dataset should be generated with known ground truth.

## 6.3 Synthetic dataset generation

Recommended pipeline:

```text
GNU Radio signal generator
 ↓
Choose modulation
 ↓
Choose FEC
 ↓
Choose interleaving
 ↓
Apply channel impairments
 ├── AWGN
 ├── frequency offset
 ├── timing offset
 ├── phase offset
 ├── fading where required
 └── gain variation
 ↓
Generate IQ
 ↓
Optionally create WAV representation
 ↓
Store labels
```

Example metadata:

```json
{
  "modulation": "QPSK",
  "fec": "convolutional",
  "interleaving": "block",
  "code_rate": "1/2",
  "symbol_rate": 250000,
  "snr_db": 10,
  "frequency_offset_hz": 1500,
  "seed": 42
}
```

## 6.4 Dataset split

Use separate:

- training
- validation
- test

sets.

Do not generate near-identical samples into both train and test.

Split by generation seeds and parameter combinations to test generalization.

## 6.5 Feature pipeline

```text
IQ
 ↓
DSP preprocessing
 ↓
Feature extraction
 ↓
Feature vector / tensors
 ↓
ML model
 ↓
probabilities
```

Possible feature groups:

- spectral
- temporal
- amplitude
- phase
- frequency
- constellation
- statistical
- cyclostationary

## 6.6 Model selection

Do not assume CNN/ResNet/LSTM/GRU are all necessary.

Start with a baseline:

- classical ML on engineered features

Then evaluate:

- CNN on signal representations
- 1D CNN on IQ sequences
- spectrogram-based CNN

Use sequence models only if they provide measurable improvement.

The architecture can mention advanced models, but the MVP should avoid unnecessary model complexity.

## 6.7 ML outputs

Example:

```text
Modulation:
QPSK 0.94
8PSK 0.04
16QAM 0.02

FEC candidates:
Convolutional 0.78
LDPC          0.16
RS            0.06

Interleaving:
Block         0.71
None          0.18
Convolutional 0.11
```

These are candidate probabilities, not proof.

## 6.8 DSP + ML reconciliation

Use a fusion strategy:

```text
DSP estimate
      +
ML prediction
      ↓
Candidate generation/ranking
      ↓
Decoder validation
```

For example, a symbol-rate estimate from DSP can constrain the demodulator search.

The recovery engine should have the final say on whether a complete hypothesis actually works.

## 6.9 Model governance

Record:

- model name
- model version
- training dataset version
- preprocessing version
- feature version
- test accuracy
- confusion matrix
- known limitations

Never ship a model without knowing which training distribution produced it.
