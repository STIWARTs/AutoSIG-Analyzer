For **SIH PS 26147**, the cleanest technical interpretation is a **hybrid DSP + AI/ML signal-analysis and recovery system**. The important distinction is that DSP performs deterministic signal processing and recovery, while AI/ML assists automated identification and hypothesis ranking.

# Complete End-to-End Process

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         0. INPUT ACQUISITION                         │
│                                                                      │
│                    .IQ / .WAV Signal File                           │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     1. INPUT VALIDATION & PARSING                    │
│                                                                      │
│ File format → Metadata → Sample format → File integrity             │
│ Sample rate / Center frequency / Channels / Bit depth / Endianness   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    2. SIGNAL REPRESENTATION                          │
│                                                                      │
│ .IQ  → Complex samples: I + jQ                                      │
│ .WAV → Real samples / recorded signal representation                │
│                                                                      │
│ Convert to internal unified signal representation                   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       3. DSP PREPROCESSING                           │
│                                                                      │
│ DC Offset Removal                                                    │
│ IQ Imbalance Correction                                              │
│ Filtering / Band Selection                                           │
│ Noise Reduction                                                      │
│ Normalization / AGC                                                  │
│ Resampling                                                           │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                 4. SIGNAL DETECTION & SEGMENTATION                   │
│                                                                      │
│ Energy Detection / Thresholding                                     │
│ Burst Detection                                                      │
│ Signal-of-Interest Identification                                   │
│ Multiple-signal segmentation                                        │
│ Active-region extraction                                            │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════╗
║                    5. DSP FEATURE EXTRACTION                         ║
║                                                                      ║
║ Time Domain                                                         ║
║   Amplitude / Phase / Frequency / Envelope                           ║
║                                                                      ║
║ Frequency Domain                                                    ║
║   FFT / PSD / Occupied Bandwidth / Spectral Peaks                   ║
║                                                                      ║
║ Time-Frequency Domain                                               ║
║   STFT / Spectrogram / Waterfall                                     ║
║                                                                      ║
║ Modulation Features                                                 ║
║   Constellation / Phase transitions / Higher-order statistics       ║
║                                                                      ║
║ Advanced Features                                                   ║
║   Cyclostationary features / instantaneous frequency                ║
╚══════════════════════════════════╤═══════════════════════════════════╝
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   6. DSP PARAMETER ESTIMATION                        │
│                                                                      │
│ Sampling Frequency (Fs)                                             │
│ Bandwidth                                                            │
│ SNR                                                                  │
│ Carrier Frequency / Frequency Offset                                │
│ Symbol Rate                                                          │
│ Pulse characteristics                                                │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
                         EXTRACTED FEATURES
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
       ┌─────────────────────────┐   ┌─────────────────────────────┐
       │ 7A. ML TRAINING         │   │ 7B. ML INFERENCE             │
       │                         │   │                             │
       │ GNU Radio Synthetic     │   │ Unknown signal features    │
       │ Signal Generation       │   │            ↓                │
       │                         │   │ Trained ML models           │
       │ Known Ground Truth:     │   │            ↓                │
       │ Modulation              │   │ Modulation classification   │
       │ FEC                     │   │ FEC candidate prediction    │
       │ Interleaving            │   │ Interleaving prediction     │
       │ SNR / offsets           │   │ Confidence estimation       │
       └───────────┬─────────────┘   └──────────────┬──────────────┘
                   │                                │
                   ▼                                │
          Labeled Dataset                           │
                   │                                │
                   ▼                                │
             Model Training                         │
                   │                                │
                   ▼                                │
            Trained Models ─────────────────────────┘
                                                    │
                                                    ▼
╔══════════════════════════════════════════════════════════════════════╗
║                 8. PARAMETER IDENTIFICATION                         ║
║                                                                      ║
║ DSP estimates + ML predictions are combined                         ║
║                                                                      ║
║ Example:                                                            ║
║   Modulation: QPSK       → 92%                                      ║
║   FEC: Convolutional     → 81%                                      ║
║   Interleaving: Block    → 76%                                      ║
║                                                                      ║
║ ML does NOT blindly determine the final answer.                     ║
╚══════════════════════════════════╤═══════════════════════════════════╝
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════╗
║                  9. HYPOTHESIS GENERATION                           ║
║                                                                      ║
║ Combine probable parameters into complete decoding configurations   ║
║                                                                      ║
║ H1 = QPSK + Convolutional FEC + Block Interleaving                  ║
║ H2 = QPSK + LDPC + Block Interleaving                               ║
║ H3 = 8PSK + Convolutional FEC + Block Interleaving                  ║
║                                                                      ║
║ Rank candidates and select TOP-K (e.g. Top-3)                       ║
╚══════════════════════════════════╤═══════════════════════════════════╝
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  10. SIGNAL SYNCHRONIZATION                          │
│                                                                      │
│ Coarse/Fine Frequency Offset Correction                             │
│ Carrier Recovery                                                    │
│ Phase Recovery                                                      │
│ Symbol Timing Recovery                                              │
│ Matched Filtering                                                   │
│ Equalization where required                                         │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     11. DEMODULATION                                 │
│                                                                      │
│ Selected according to hypothesis:                                   │
│                                                                      │
│ FSK → Frequency discrimination / symbol detection                    │
│ PSK → BPSK / QPSK / 8PSK phase detection                            │
│ QAM → QAM symbol detection                                          │
│                                                                      │
│ Output → Hard bits OR Soft decision values                          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   12. DE-INTERLEAVING                                │
│                                                                      │
│ According to candidate hypothesis:                                  │
│                                                                      │
│ Block Interleaving                                                  │
│ Convolutional Interleaving                                          │
│ Diagonal Interleaving                                               │
│ Pseudo-Random Interleaving                                          │
│                                                                      │
│ Recover original ordering of coded bits                              │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     13. FEC DECODING                                 │
│                                                                      │
│ Convolutional Code → Viterbi Decoder                                │
│ Reed-Solomon → RS Block Decoder                                     │
│ Concatenated Codes → Sequential decoding                            │
│ LDPC → LDPC Decoder                                                  │
│                                                                      │
│ Output → Corrected bitstream                                        │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════╗
║                     14. VALIDATION ENGINE                            ║
║                                                                      ║
║ Check whether the current hypothesis actually explains the signal.  ║
║                                                                      ║
║ • CRC / parity checks                                               ║
║ • FEC decoder success                                               ║
║ • Syndrome/check validity                                           ║
║ • Bit statistics                                                    ║
║ • Frame consistency                                                 ║
║ • Preamble correlation                                              ║
║ • Header consistency                                                ║
║                                                                      ║
║              ┌──────────────────────┐                               ║
║              │ Hypothesis Valid?    │                               ║
║              └──────────┬───────────┘                               ║
║                         │                                            ║
║                 YES     │      NO                                   ║
║                  ↓      │       ↓                                   ║
║             Accept      │   Next candidate                          ║
║                         │       ↓                                   ║
║                         │   Retry limit?                             ║
║                         │      │                                     ║
║                         │     YES                                   ║
║                         │      ↓                                     ║
║                         │ Low-confidence / Unclassified              ║
╚═════════════════════════╪════════════════════════════════════════════╝
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  15. BITSTREAM PROCESSING                            │
│                                                                      │
│ Corrected bitstream                                                  │
│      ↓                                                               │
│ Bit packing / unpacking                                              │
│ Descrambling if applicable                                           │
│ Frame synchronization                                                │
│ Preamble detection                                                   │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    16. BITSTREAM CORRELATION                         │
│                                                                      │
│ Known sequence / reference pattern correlation                       │
│ Preamble detection                                                   │
│ Header detection                                                     │
│ Frame boundary identification                                        │
│ Repeated-pattern analysis                                            │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                  17. HEADER / PAYLOAD IDENTIFICATION                 │
│                                                                      │
│                    ┌───────────────┐                                 │
│                    │  Bitstream    │                                 │
│                    └───────┬───────┘                                 │
│                            ↓                                          │
│                  ┌──────────────────┐                                │
│                  │ Preamble / Sync  │                                │
│                  └────────┬─────────┘                                │
│                           ↓                                          │
│                  ┌──────────────────┐                                │
│                  │     HEADER       │                                │
│                  └────────┬─────────┘                                │
│                           ↓                                          │
│                  ┌──────────────────┐                                │
│                  │     PAYLOAD      │                                │
│                  └──────────────────┘                                │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
╔══════════════════════════════════════════════════════════════════════╗
║                         18. FINAL REPORT                             ║
║                                                                      ║
║ Signal Information                                                  ║
║   • Input file / recording information                              ║
║   • Sampling frequency                                              ║
║   • Bandwidth                                                       ║
║   • SNR                                                             ║
║   • Carrier/frequency offset                                        ║
║   • Symbol rate                                                     ║
║                                                                      ║
║ Classification                                                      ║
║   • Modulation                                                      ║
║   • FEC                                                             ║
║   • Interleaving                                                    ║
║   • Confidence scores                                               ║
║                                                                      ║
║ Visual Analysis                                                     ║
║   • Waveform                                                        ║
║   • FFT / Spectrum                                                  ║
║   • Waterfall / Spectrogram                                         ║
║   • Constellation                                                    ║
║   • Eye diagram                                                     ║
║                                                                      ║
║ Recovery                                                            ║
║   • Demodulated bits                                                ║
║   • FEC result                                                      ║
║   • Correlation result                                              ║
║   • Header / payload boundaries                                     ║
║                                                                      ║
║ Export → PDF / JSON / CSV / TXT                                    ║
╚══════════════════════════════════════════════════════════════════════╝
```

# What each major layer actually does

## Layer 0 — Input handling

The application accepts:

```text
.IQ
.WAV
```

The first job is **not DSP or AI**. It is determining whether the file is usable.

For example:

```text
File
 ↓
Extension check
 ↓
Header/container parsing
 ↓
Sample format detection
 ↓
Metadata extraction
 ↓
Integrity check
```

Potential invalid cases:

```text
Corrupted file
Unsupported format
Missing WAV metadata
Unknown IQ datatype
Invalid sample count
Insufficient samples
```

The GUI should report these before expensive processing begins.

---

# Layer 1 — DSP Signal Processing

This is where the raw samples become **signal characteristics**.

### Example

Raw IQ:

```text
I0,Q0
I1,Q1
I2,Q2
I3,Q3
...
```

DSP can calculate:

```text
Amplitude
Phase
Frequency
Power
Spectrum
Bandwidth
SNR
```

For example, FFT transforms:

```text
Time-domain samples
        ↓
       FFT
        ↓
Frequency-domain representation
```

This gives you the spectrum.

STFT gives:

```text
Time + Frequency
        ↓
Spectrogram / Waterfall
```

This is one of the explicit visualization requirements in the PS.

---

# Layer 2 — AI/ML Parameter Identification

This is where your system becomes **automated**.

The ML model receives features such as:

```text
Spectral features
Constellation features
Phase statistics
Amplitude statistics
Higher-order statistics
Cyclostationary features
```

and predicts things like:

```text
Modulation:
QPSK 92%
8PSK  5%
16QAM 3%
```

Potentially:

```text
FEC:
Convolutional 81%
LDPC          13%
RS             6%
```

and:

```text
Interleaving:
Block          76%
None           17%
Convolutional   7%
```

But these are **candidate predictions**, not guaranteed truth.

---

# Layer 3 — Hypothesis Engine

This is the bridge between **AI/ML and DSP recovery**.

ML might independently predict:

```text
QPSK
Convolutional FEC
Block Interleaving
```

The hypothesis engine combines them:

```text
H1 =
QPSK
+
Convolutional FEC
+
Block Interleaving
```

Then another:

```text
H2 =
QPSK
+
LDPC
+
Block Interleaving
```

Then:

```text
H3 =
8PSK
+
Convolutional
+
Block
```

Only the **Top-K candidates** should be tested.

This is critical for keeping computation bounded.

---

# Layer 4 — DSP Recovery

Now the system asks:

> "Can this hypothesis actually recover a valid digital stream?"

For H1:

```text
QPSK
 ↓
Synchronization
 ↓
QPSK Demodulator
 ↓
De-interleaver
 ↓
Viterbi
 ↓
Corrected bits
```

Then validation.

If it fails:

```text
H1 → FAIL
```

Try:

```text
H2 → FAIL
```

Then:

```text
H3 → SUCCESS
```

Now H3 becomes the best-supported interpretation.

---

# Layer 5 — Bitstream analysis

Once you have corrected bits:

```text
010011010101...
```

you can search for:

```text
Preamble
Sync pattern
Header
Frame boundaries
Payload
```

Correlation is useful here.

For example, if you know or hypothesize a preamble:

```text
Known:
1010101111001101

Received:
...1010101111001101...
             ↑
          correlation
```

A strong correlation indicates a potential frame boundary.

---

# Layer 6 — Report

The final report should not simply say:

```text
Modulation: QPSK
```

It should provide evidence:

```text
SIGNAL ANALYSIS REPORT

Input:
capture_001.iq

Sampling Rate:
2.000 MHz

Estimated Bandwidth:
~400 kHz

Estimated SNR:
15.2 dB

Symbol Rate:
~250 kSym/s

Modulation:
QPSK
Confidence: 92%

FEC:
Convolutional
Confidence: 81%

Interleaving:
Block
Confidence: 76%

Recovery:
SUCCESS

FEC Validation:
PASS

Bit Correlation:
0.94

Header:
Detected

Payload:
Detected
```

And attach:

```text
Waveform
Spectrum
Waterfall
Constellation
Eye diagram
Bitstream
Processing log
```

---

# The most important conceptual flow

If you need to explain the entire project to a judge in **30 seconds**, use this:

> **"We take raw IQ or WAV recordings, validate and normalize them, then apply DSP techniques such as filtering, FFT, STFT, signal detection and feature extraction. These features are passed to AI/ML models to classify modulation and generate ranked FEC and interleaving candidates. A bounded hypothesis engine selects the top candidates and passes them through a DSP recovery chain consisting of synchronization, demodulation, de-interleaving and FEC decoding. Each result is validated using decoder checks, correlation and frame consistency. The best validated result is then processed for header/payload identification and presented through a GUI with a detailed signal-analysis report."**

That is the **complete technical story of PS 26147**.

And one architectural principle should remain fixed:

```text
                    INPUT
                      ↓
                INPUT HANDLING
                      ↓
                     DSP
                      ↓
                  FEATURES
                      ↓
                 AI / ML
                      ↓
               HYPOTHESES
                      ↓
                DSP RECOVERY
                      ↓
                 VALIDATION
                      ↓
               BIT ANALYSIS
                      ↓
                  REPORT
```

**DSP is the foundation, AI/ML is the intelligence for automated identification/ranking, and the recovery DSP validates whether the AI-generated interpretation actually works.**
