# 1. Problem Understanding and Thinking Approach

## 1.1 What the problem is actually asking

The PS starts with raw signals collected from the air. These recordings may span HF, VHF and UHF applications and can be stored as `.IQ` or `.wav`.

The difficulty is that recordings from different sensors, locations and acquisition configurations may not contain enough metadata to directly tell an analyst:

- sampling frequency
- bandwidth
- carrier/frequency offset
- symbol rate
- modulation
- FEC
- interleaving configuration

The proposed software should make the signal more information-rich by automatically analyzing the raw samples and recovering useful parameters and bit-level information.

## 1.2 Convert the PS into engineering requirements

The PS can be decomposed into five layers:

### Layer A — Input

Accept:

- `.IQ`
- `.wav`

Validate:

- file structure
- sample type
- channel count
- sample rate if present
- metadata
- file size
- numeric integrity

### Layer B — Observation and parameter extraction

Generate:

- waveform
- FFT/spectrum
- waterfall/spectrogram
- constellation
- eye diagram where meaningful
- SNR
- bandwidth
- sample rate
- symbol rate
- carrier/frequency offset

### Layer C — Signal interpretation

Classify or hypothesize:

- FSK
- PSK
- QAM
- FEC type
- interleaving type

### Layer D — Digital recovery

Support the PS-listed families:

- FSK/PSK/QAM demodulation
- Block de-interleaving
- Convolutional de-interleaving
- Diagonal de-interleaving
- Pseudo-random de-interleaving
- Convolutional-code Viterbi decoding
- Reed-Solomon
- Concatenated codes
- LDPC

### Layer E — Bit-level analysis

Produce:

- cleaned/corrected bitstream
- bit-stream correlation
- preamble/header detection
- header/payload boundary
- payload extraction
- report/export

## 1.3 The key design insight

The signal should not immediately enter a decoder.

First:

```text
Observe → Measure → Extract features → Classify → Hypothesize → Recover → Validate
```

This is more robust than hard-coding one signal format.

## 1.4 Why DSP and ML are both needed

### DSP

DSP is deterministic mathematical processing of sampled signals.

Examples:

- filtering
- FFT
- STFT
- timing recovery
- carrier recovery
- symbol-rate estimation
- demodulation

### AI/ML

ML is useful when the relationship between signal features and signal class is difficult to encode using simple rules.

Examples:

- modulation classification
- ranking FEC candidates
- ranking interleaving candidates
- confidence estimation

### Recovery engine

The recovery engine verifies an ML hypothesis using actual decoding results.

```text
ML: "QPSK is likely."
        ↓
DSP: demodulate as QPSK
        ↓
Try candidate FEC/interleaver
        ↓
Validation
        ↓
Accept or reject
```

## 1.5 Why a hypothesis system is necessary

Unknown signals create ambiguity.

Example:

```text
Candidate 1:
QPSK + convolutional FEC + block interleaving → 92%

Candidate 2:
QPSK + LDPC + no interleaving → 76%

Candidate 3:
8PSK + convolutional FEC + block interleaving → 58%
```

Do not test every theoretical combination.

Use **Top-K candidate pruning**, e.g. Top-3, then validate those candidates.

## 1.6 What success means

A successful analysis does not necessarily mean the system understands the semantic meaning of payload data.

Success means the system can produce a defensible chain such as:

```text
Signal detected
→ parameters estimated
→ modulation classified
→ synchronization succeeded
→ bits recovered
→ de-interleaving succeeded
→ FEC validation passed
→ header/preamble detected
→ report generated
```

If this chain cannot be established, the system should report **low confidence / unclassified**, not invent an answer.
