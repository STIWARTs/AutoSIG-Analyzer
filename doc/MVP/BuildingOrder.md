# Exact Build Order and Team Split

## Build order

### 1. Foundation
- repository
- schemas
- configuration
- logging

### 2. Input
- IQ reader
- WAV reader
- validation
- canonical representation

### 3. Visualization
- waveform
- FFT
- waterfall
- constellation

### 4. DSP
- SNR
- bandwidth
- frequency offset
- symbol rate

### 5. Hard-coded known path

Before ML, make this work:

```text
known QPSK
→ synchronization
→ demodulation
→ block deinterleave
→ convolutional FEC
→ Viterbi
→ validation
```

### 6. Synthetic dataset
Generate the same signal family with known labels.

### 7. ML
Train modulation classifier.

### 8. Candidate engine
Add Top-K ranking and validation.

### 9. GUI integration
Connect complete engine.

### 10. Reporting
PDF/JSON/CSV.

### 11. Extensions
Only now add FSK/QAM/RS/LDPC/other interleavers.

## Team split

### DSP member
- preprocessing
- FFT/STFT
- estimators
- synchronization

### ML member
- GNU Radio dataset
- features
- model
- evaluation

### Recovery member
- demodulators
- interleavers
- FEC
- validation
- correlation

### Application member
- C# GUI
- API
- visualization
- reports
- packaging

## Integration rule

Main branch must remain runnable.

Maintain one daily test:

```text
synthetic signal
→ full pipeline
→ expected payload
```
