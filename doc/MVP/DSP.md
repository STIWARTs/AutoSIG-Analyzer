# DSP Pipeline

## 5.1 DSP definition

Digital Signal Processing is the mathematical processing of sampled signals.

In this project DSP is responsible for transforming raw samples into measurable signal characteristics and recoverable symbols/bits.

## 5.2 Preprocessing

Typical sequence:

```text
Raw samples
 ↓
DC removal
 ↓
IQ imbalance correction where applicable
 ↓
Filtering
 ↓
Gain/normalization
 ↓
Optional resampling
 ↓
Signal detection
```

Do not apply every operation blindly. Each operation should be enabled based on input characteristics.

## 5.3 Filtering

Possible filters:

- low-pass
- band-pass
- notch
- matched filtering where a waveform model is known

Record:

- filter type
- cutoff frequencies
- order
- sample rate

## 5.4 Signal detection

For long recordings:

```text
Long recording
 ↓
energy/statistical detection
 ↓
candidate regions
 ↓
merge nearby regions
 ↓
extract signal segments
```

This prevents the ML model and decoder from processing unnecessary noise.

## 5.5 FFT and spectrum

FFT provides frequency-domain representation.

Outputs:

- frequency axis
- magnitude/power
- dominant components
- occupied bandwidth estimates

Important distinction:

**FFT does not magically reveal the original sample rate if the file does not contain enough information.**

Sample rate may come from:

- file metadata
- acquisition metadata
- known recording configuration
- inference/estimation under constrained assumptions

## 5.6 STFT / waterfall

STFT computes frequency content over time.

Waterfall view helps identify:

- bursts
- frequency hopping
- intermittent signals
- frequency drift
- occupied regions
- time-varying behavior

## 5.7 Constellation

For coherent digital modulation, estimate symbols and plot I/Q coordinates.

Useful for:

- BPSK
- QPSK
- PSK
- QAM

The constellation should normally be viewed after appropriate synchronization; otherwise rotation and frequency offset can obscure clusters.

## 5.8 Eye diagram

Useful for assessing:

- timing
- inter-symbol interference
- pulse shaping
- noise

It is supportive, not a universal classifier.

## 5.9 Parameter estimation

Target parameters:

- sampling frequency
- occupied bandwidth
- SNR
- carrier/frequency offset
- symbol rate

### Symbol rate

Possible DSP methods include:

- autocorrelation
- spectral line/feature analysis
- cyclostationary analysis
- timing recovery feedback

Use one primary estimator in the architecture and use other estimates as cross-checks.

## 5.10 Synchronization

Synchronization is a real engineering module.

Submodules can include:

- coarse frequency estimation
- fine frequency correction
- carrier recovery
- phase recovery
- timing recovery
- matched filtering
- equalization where appropriate

For example, depending on the signal:

- Gardner timing recovery
- Mueller-Muller timing recovery
- Costas-loop style carrier recovery

The exact algorithm is modulation/channel dependent.

## 5.11 DSP output contract

The DSP layer should return structured data:

```json
{
  "sample_rate": {"value": 2000000, "confidence": 0.99},
  "bandwidth_hz": {"value": 400000, "confidence": 0.91},
  "symbol_rate": {"value": 250000, "confidence": 0.88},
  "snr_db": {"value": 17.2, "confidence": 0.94},
  "frequency_offset_hz": {"value": 1200, "confidence": 0.82},
  "features": {}
}
```

Values are examples only; real estimates must come from processing.
