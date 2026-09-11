Yes. For the SIH PS 26147, I would **not try to implement every modulation + every FEC + every interleaver in the first prototype**. Build a complete vertical slice that actually takes an `.IQ/.WAV` file and produces a defensible analysis report.

# SIH PS 26147 — Working MVP Plan

## 1. What the MVP must demonstrate

Your MVP should answer this question:

> **“Given an unknown IQ/WAV signal recording, can our application automatically analyze it, identify likely signal parameters, recover the bitstream, validate the recovery, and generate a report?”**

The demo should therefore have this flow:

```text
                USER
                 │
                 ▼
        ┌─────────────────┐
        │ Upload IQ / WAV │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ Input Validation│
        └────────┬────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │ DSP SIGNAL PROCESSING  │
        │                        │
        │ • Waveform             │
        │ • FFT / Spectrum       │
        │ • Spectrogram          │
        │ • SNR                  │
        │ • Bandwidth            │
        │ • Frequency Offset     │
        │ • Symbol Rate          │
        │ • Constellation        │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ AI / ML PARAMETER      │
        │ IDENTIFICATION         │
        │                        │
        │ Modulation             │
        │ FEC candidate          │
        │ Interleaver candidate  │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ HYPOTHESIS ENGINE      │
        │                        │
        │ H1: QPSK + Conv + Block│
        │ H2: QPSK + LDPC + Block│
        │ H3: 8PSK + Conv + Block│
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ DSP SIGNAL RECOVERY    │
        │                        │
        │ Synchronization        │
        │ Demodulation           │
        │ De-interleaving        │
        │ FEC decoding           │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ VALIDATION ENGINE      │
        │                        │
        │ CRC / parity           │
        │ FEC validity           │
        │ correlation            │
        │ frame consistency      │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ BITSTREAM ANALYSIS     │
        │                        │
        │ Preamble               │
        │ Header                 │
        │ Payload                │
        └───────────┬────────────┘
                    │
                    ▼
        ┌────────────────────────┐
        │ FINAL ANALYSIS REPORT  │
        └────────────────────────┘
```

That is enough to make the project look like an actual working automated signal-analysis system rather than a collection of graphs.

---

# 2. Most important MVP decision

I recommend implementing **one complete reliable signal path first**.

### Primary demonstration

Use:

```text
QPSK
  ↓
Block Interleaving
  ↓
Convolutional FEC
  ↓
Viterbi Decoder
  ↓
Bitstream
  ↓
Known Header/Preamble Correlation
```

Why QPSK?

Because it gives you enough complexity to demonstrate:

* modulation classification
* carrier/phase synchronization
* constellation
* symbol recovery
* soft decisions
* convolutional coding
* Viterbi
* interleaving
* bit recovery
* correlation
* validation

You can later add:

```text
BPSK
8PSK
FSK
QAM
LDPC
Reed-Solomon
```

without redesigning the architecture.

---

# 3. The technology architecture

Since your requirement is a **desktop application with C#/.NET**, I would use:

```text
                 C# .NET Desktop Application
                         │
                         │
             ┌───────────┴───────────┐
             │                       │
          UI Layer              Application Layer
             │                       │
             └───────────┬───────────┘
                         │
                    Python DSP
                         │
                 ┌───────┴───────┐
                 │               │
              NumPy           SciPy
                 │               │
              DSP/ML          Signal
                             Processing
                 │
                 ▼
             ML Models
                 │
                 ▼
              Results
```

### Suggested stack

| Component                | Technology                         |
| ------------------------ | ---------------------------------- |
| Desktop UI               | C# / .NET                          |
| UI framework             | WPF                                |
| Application architecture | MVVM                               |
| DSP                      | Python                             |
| Numerical processing     | NumPy                              |
| Signal processing        | SciPy                              |
| FFT                      | NumPy/SciPy                        |
| ML                       | PyTorch or scikit-learn            |
| Signal generation        | GNU Radio                          |
| Visualization            | Python-generated data + WPF charts |
| FEC                      | Python implementation/library      |
| IPC                      | Local REST API                     |
| API server               | FastAPI                            |
| Database                 | SQLite                             |
| Report                   | HTML/PDF                           |
| Packaging                | .NET + Python environment          |

I would **not put the entire DSP implementation directly inside C#** for the MVP.

Keep the responsibilities clean:

```text
C# = application
Python = signal intelligence
GNU Radio = signal generation/training data
```

---

# 4. Project structure

Build the repository approximately like this:

```text
SIH-26147/
│
├── desktop/
│   ├── SignalAnalyzer.sln
│   │
│   └── SignalAnalyzer/
│       ├── Views/
│       │   ├── Dashboard.xaml
│       │   ├── Upload.xaml
│       │   ├── Analysis.xaml
│       │   ├── Recovery.xaml
│       │   └── Report.xaml
│       │
│       ├── ViewModels/
│       │   ├── DashboardViewModel.cs
│       │   ├── UploadViewModel.cs
│       │   ├── AnalysisViewModel.cs
│       │   └── ReportViewModel.cs
│       │
│       ├── Models/
│       │   ├── SignalFile.cs
│       │   ├── SignalParameters.cs
│       │   ├── MLResult.cs
│       │   ├── Hypothesis.cs
│       │   └── AnalysisResult.cs
│       │
│       ├── Services/
│       │   ├── PythonService.cs
│       │   ├── AnalysisService.cs
│       │   └── ReportService.cs
│       │
│       └── App.xaml
│
├── backend/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── upload.py
│   │   ├── analysis.py
│   │   └── report.py
│   │
│   ├── dsp/
│   │   ├── preprocessing.py
│   │   ├── detection.py
│   │   ├── spectrum.py
│   │   ├── features.py
│   │   ├── synchronization.py
│   │   ├── demodulation.py
│   │   └── parameters.py
│   │
│   ├── ml/
│   │   ├── features.py
│   │   ├── classifier.py
│   │   ├── inference.py
│   │   └── models/
│   │
│   ├── recovery/
│   │   ├── interleaver.py
│   │   ├── fec.py
│   │   ├── viterbi.py
│   │   └── validator.py
│   │
│   ├── correlation/
│   │   ├── preamble.py
│   │   └── header.py
│   │
│   └── reports/
│       └── generator.py
│
├── datasets/
│   ├── generated/
│   ├── validation/
│   └── test/
│
├── gnuradio/
│   ├── qpsk_generator.grc
│   ├── bpsk_generator.grc
│   └── dataset_generator.py
│
├── docs/
│   ├── architecture.md
│   ├── mvp.md
│   ├── dsp.md
│   ├── ml.md
│   ├── recovery.md
│   └── testing.md
│
├── requirements.txt
└── README.md
```

This separation will also make your final explanation to judges much easier.

---

# 5. Stage 1 — File Upload

The application starts with:

```text
Select Signal File

[ Browse ]

Supported:
✓ .IQ
✓ .WAV
```

When selected:

```text
sample.iq
```

the application should calculate:

```text
File name
File size
File type
Number of samples
Sample format
Sample rate
Channels
Duration
```

For WAV:

```text
Sample rate
Channels
Bit depth
Number of frames
Duration
```

For IQ:

```text
Sample format
I/Q arrangement
Number of samples
Sample rate if metadata exists
Center frequency if metadata exists
```

---

# 6. Stage 2 — Input validation

Before DSP begins:

```text
                 FILE
                   │
                   ▼
           Extension Check
                   │
                   ▼
           Format Validation
                   │
                   ▼
           Metadata Parsing
                   │
                   ▼
          Sample Format Check
                   │
                   ▼
            Data Integrity
                   │
          ┌────────┴────────┐
          │                 │
        Valid             Invalid
          │                 │
          ▼                 ▼
      Continue           Error
```

Your application should explicitly show:

```text
Input validation
✓ File format valid
✓ Sample data readable
✓ Sample count valid
✓ Sample rate detected
✓ No corruption detected
```

This is useful during the demo because it shows that you are not simply throwing a file into an ML model.

---

# 7. Stage 3 — Unified signal representation

Internally convert everything to a standard representation.

For IQ:

```python
x[n] = I[n] + jQ[n]
```

So:

```text
I:  0.23  0.41  -0.12 ...
Q: -0.14  0.22   0.51 ...
```

becomes:

```text
0.23 - 0.14j
0.41 + 0.22j
-0.12 + 0.51j
...
```

For a suitable real-valued WAV signal:

```text
x[n] = audio_sample[n]
```

If a WAV contains stereo IQ:

```text
Left channel  → I
Right channel → Q
```

This interpretation must be based on the actual recording format, not assumed for every WAV.

---

# 8. Stage 4 — DSP preprocessing

Implement these first:

### 8.1 DC removal

```text
x[n] = x[n] - mean(x)
```

### 8.2 Normalization

Normalize amplitude so that different recordings have comparable scale.

### 8.3 Filtering

Implement configurable:

```text
Low-pass
Band-pass
Notch
```

### 8.4 Optional resampling

If required:

```text
Original Fs
     ↓
Resampler
     ↓
Standard Fs
```

### 8.5 IQ correction

For IQ recordings, eventually support:

```text
I/Q imbalance
DC offset
image rejection
```

For MVP, DC removal + normalization + filtering is enough.

---

# 9. Stage 5 — Signal detection

Do not immediately process the entire recording.

Find where the signal exists.

Example:

```text
Amplitude

        SIGNAL
          ███████
          ███████
          ███████
__________███████______________
                         noise

Time ──────────────────────────>
```

Implement:

```text
Energy estimation
       ↓
Noise floor
       ↓
Threshold
       ↓
Active signal regions
```

Output:

```json
{
  "signal_start": 124000,
  "signal_end": 198000,
  "duration": 74000
}
```

---

# 10. Stage 6 — DSP visualization

This is one of the most important parts of your GUI.

Show four primary plots.

## A. Time waveform

```text
Amplitude
   │
   │     /\      /\
   │ /\ /  \ /\ /  \
───┼──────────────────── Time
```

## B. FFT / spectrum

```text
Power
 │
 │             /\
 │            /  \
 │___________/    \________
 └───────────────────────── Frequency
```

## C. Waterfall

```text
Frequency →
────────────────────
███████
 ███████
  ██████
  ██████
────────────────────
Time ↓
```

## D. Constellation

For QPSK:

```text
        Q
        │
   ×    │    ×
        │
────────┼──────── I
        │
   ×    │    ×
        │
```

These four visualizations will make your application immediately understandable to judges.

---

# 11. Stage 7 — Parameter extraction

Now calculate the deterministic DSP parameters.

At minimum:

```text
Sampling Frequency
Signal Bandwidth
Center/Frequency Offset
SNR
Symbol Rate
```

Example UI:

```text
SIGNAL PARAMETERS

Sampling Rate       2.000 MHz
Estimated Bandwidth  410 kHz
Estimated SNR        14.7 dB
Symbol Rate          100 kSym/s
Frequency Offset     +2.3 kHz

Detection Confidence 0.94
```

---

# 12. How to estimate each parameter

## Sampling rate

Usually obtained directly from:

```text
WAV metadata
```

or IQ metadata/configuration.

Do **not** claim ML discovered the physical sample rate when the recording metadata provides it.

---

## Bandwidth

From PSD/FFT:

```text
Noise floor
    ↓
occupied spectral region
    ↓
bandwidth
```

For example:

```text
Lower frequency = 1.82 MHz
Upper frequency = 2.23 MHz

Bandwidth ≈ 410 kHz
```

---

## SNR

Estimate:

```text
Signal Power
────────────
Noise Power
```

then:

```text
SNR(dB) = 10 log10(Psignal / Pnoise)
```

---

## Symbol rate

This is more involved.

Possible MVP approaches:

```text
timing spectrum
      +
cyclostationary analysis
      +
spectral characteristics
      ↓
symbol-rate candidate
```

You should label this:

> Estimated Symbol Rate

rather than pretending it is guaranteed.

---

# 13. Stage 8 — ML classifier

Now introduce AI/ML.

For the MVP, start with:

```text
Modulation Classifier
```

Classes:

```text
BPSK
QPSK
8PSK
QAM
FSK
```

You can expand later.

---

# 14. Training dataset

This is a critical part of your SIH project.

Real intercepted signals usually don't provide:

```text
"this is QPSK"
"this uses convolutional code"
"this uses block interleaving"
```

as ground truth.

So generate synthetic training signals.

Use GNU Radio:

```text
Random Bits
    │
    ▼
FEC Encoder
    │
    ▼
Interleaver
    │
    ▼
Modulator
    │
    ▼
Channel
    │
    ├── Noise
    ├── Frequency Offset
    ├── Timing Offset
    └── Phase Offset
    │
    ▼
IQ Samples
```

And because you created the signal, you know the ground truth.

Example:

```text
sample_0001.iq

Modulation = QPSK
FEC = convolutional
Interleaver = block
SNR = 10 dB
Frequency offset = 2 kHz
```

This is extremely useful for training and evaluation.

---

# 15. Dataset generation strategy

Do not generate only perfect signals.

Generate variation.

For QPSK:

```text
SNR:
-5
0
5
10
15
20
25 dB
```

Frequency offset:

```text
-5 kHz
-2 kHz
0
+2 kHz
+5 kHz
```

Timing offsets:

```text
small random offsets
```

Phase offsets:

```text
random
```

Then your model learns robustness rather than memorizing one perfect constellation.

---

# 16. ML input

Don't necessarily feed raw IQ directly into your first model.

For a simpler MVP:

```text
IQ
 │
 ├── FFT
 ├── Spectrogram
 ├── Constellation
 ├── amplitude statistics
 ├── phase statistics
 └── higher-order features
       │
       ▼
     Features
       │
       ▼
    Classifier
```

Then:

```text
QPSK     92%
8PSK      4%
BPSK      3%
QAM       1%
FSK       0%
```

This is easier to explain than saying “we gave raw signals to AI.”

---

# 17. What ML should predict

For the MVP:

### Primary

```text
Modulation
```

### Secondary

Create candidate classifiers for:

```text
FEC:
Convolutional
LDPC
Reed-Solomon
None/Unknown
```

and:

```text
Interleaving:
Block
Convolutional
Diagonal
Pseudo-random
None/Unknown
```

But these secondary models can initially be simpler.

The architecture should support them even if your demonstrated accuracy is limited.

---

# 18. Stage 9 — Hypothesis generation

This is one of the most important architectural components.

Suppose ML outputs:

```text
Modulation:

QPSK        92%
8PSK         5%
BPSK         3%

FEC:

Convolutional 81%
LDPC           14%
RS              5%

Interleaver:

Block          76%
Diagonal       16%
None            8%
```

Do not simply say:

> "Answer = QPSK + convolutional + block."

Instead generate:

```text
H1
QPSK
+
Convolutional
+
Block
Score = 0.92 × 0.81 × 0.76

H2
QPSK
+
LDPC
+
Block

H3
8PSK
+
Convolutional
+
Block
```

Then:

```text
Top-K = 3
```

Only test these.

---

# 19. Why Top-K matters

Imagine:

```text
5 modulations
×
4 FECs
×
4 interleavers
```

That's:

```text
5 × 4 × 4 = 80
```

possible combinations.

You don't want to decode all 80.

Instead:

```text
ML
 ↓
Candidate ranking
 ↓
Top 3
 ↓
DSP recovery
```

This makes the system computationally manageable.

---

# 20. Stage 10 — Synchronization

This is where signal recovery starts.

For QPSK implement:

```text
Frequency correction
       ↓
Matched filtering
       ↓
Timing recovery
       ↓
Carrier/phase recovery
       ↓
Symbol sampling
```

Useful established algorithms include:

```text
Costas loop
Gardner timing recovery
Mueller-Muller timing recovery
```

You do not need to implement every synchronization algorithm for the MVP.

Pick one reliable approach for QPSK.

---

# 21. Stage 11 — QPSK demodulation

After synchronization:

```text
Complex symbols
      │
      ▼
   QPSK slicer
      │
      ▼
Soft/Hard bits
```

Example:

```text
00
01
11
10
```

Prefer **soft decisions** if your Viterbi implementation supports them.

Instead of:

```text
0
1
0
1
```

you can preserve confidence:

```text
+0.91
-0.87
+0.73
-0.42
```

This improves FEC decoding.

---

# 22. Stage 12 — De-interleaving

For your primary MVP path:

```text
Block interleaver
```

Implement:

```text
received bits
     ↓
inverse permutation
     ↓
original ordering
```

You can then add:

```text
Convolutional
Diagonal
Pseudo-random
```

as extensions.

---

# 23. Stage 13 — Convolutional FEC

Use a known simple convolutional code.

For example:

```text
Rate = 1/2
Constraint length = 7
```

Conceptually:

```text
Encoded bits
     │
     ▼
Viterbi decoder
     │
     ▼
Recovered information bits
```

The decoder should provide:

```text
decoded bits
path metric
decoder status
```

---

# 24. Stage 14 — Validation

This is where your architecture becomes much stronger.

Don't say:

```text
ML predicted QPSK
therefore signal is QPSK.
```

Instead:

```text
ML prediction
      ↓
Hypothesis
      ↓
DSP recovery
      ↓
Decoded bits
      ↓
Validation
      ↓
Accept / Reject
```

For example:

```text
H1

QPSK
Convolutional
Block

FEC validity       ✓
Header correlation ✓
Bit consistency    ✓
Frame structure    ✓

FINAL SCORE = 0.93
```

Therefore:

```text
H1 ACCEPTED
```

---

# 25. What if H1 fails?

Example:

```text
H1
QPSK + Conv + Block

FEC validation ✗
Correlation    ✗
```

Then:

```text
Try H2
```

If H2 works:

```text
H2 ACCEPTED
```

If everything fails:

```text
No hypothesis passed validation.

Result:
LOW CONFIDENCE / UNCLASSIFIED
```

This is much more realistic than forcing an answer.

---

# 26. Stage 15 — Bitstream correlation

Now implement one known synchronization pattern.

For example, during your synthetic signal generation, insert:

```text
PREAMBLE

1010101010101010...
```

Then:

```text
Recovered bits
       │
       ▼
Cross-correlation
       │
       ▼
Preamble position
```

You can display:

```text
Preamble detected
Position: 18342
Correlation: 0.94
```

This gives you an objective validation mechanism.

---

# 27. Stage 16 — Header / payload identification

Create a simple demo frame:

```text
┌──────────┬────────┬───────────────────┐
│ Preamble │ Header │ Payload           │
└──────────┴────────┴───────────────────┘
```

For example:

```text
Preamble
16 bits

Header
32 bits

Payload
variable length
```

The application can then show:

```text
BITSTREAM

0000000010101010...

     │
     ├── Preamble
     ├── Header
     └── Payload
```

This directly demonstrates the PS's bit-stream correlation requirement.

---

# 28. Final report

The report should contain:

## Input

```text
File:
capture_001.iq

Format:
Complex IQ

Samples:
2,000,000

Sample Rate:
2 MHz

Duration:
1 second
```

## Signal parameters

```text
Bandwidth       410 kHz
SNR             14.7 dB
Symbol Rate     100 kSym/s
Frequency Offset +2.3 kHz
```

## AI/ML identification

```text
Modulation

QPSK     92%
8PSK      5%
BPSK      3%
```

## Recovery hypothesis

```text
Selected:

QPSK
+
Block Interleaving
+
Convolutional FEC
```

## Validation

```text
FEC validation       PASS
Preamble correlation PASS
Frame validation     PASS
Bit consistency      PASS
```

## Output

```text
Recovered bits
Header
Payload boundaries
Confidence
```

And include:

```text
Waveform
FFT
Waterfall
Constellation
```

---

# 29. GUI structure

Your desktop application can have these pages.

```text
┌─────────────────────────────────────────────┐
│ Signal Analyzer                             │
├──────────────┬──────────────────────────────┤
│              │                              │
│ Dashboard    │                              │
│              │                              │
│ Analyze      │       MAIN CONTENT           │
│              │                              │
│ Signals      │                              │
│              │                              │
│ Parameters   │                              │
│              │                              │
│ Recovery     │                              │
│              │                              │
│ Bitstream    │                              │
│              │                              │
│ Reports      │                              │
│              │                              │
│ Settings     │                              │
└──────────────┴──────────────────────────────┘
```

---

# 30. Dashboard

Show:

```text
SIGNAL ANALYZER

Files analyzed             24
Successful recoveries      18
Low confidence              6

Latest signal

Modulation       QPSK
SNR              14.7 dB
Symbol Rate      100 kSym/s
Recovery          PASS
Confidence        93%
```

---

# 31. Analysis page

This is probably your most impressive page.

```text
┌───────────────────────────────────────────┐
│ SIGNAL ANALYSIS                           │
├───────────────────────────────────────────┤
│                                           │
│ Waveform                                  │
│ ────────────────────────────────────────  │
│                                           │
│                                           │
├──────────────────────┬────────────────────┤
│ Spectrum             │ Constellation      │
│                      │                    │
│                      │    ×       ×       │
│                      │                    │
├──────────────────────┴────────────────────┤
│ Waterfall                                │
│                                          │
└──────────────────────────────────────────┘
```

---

# 32. Parameter page

Use cards:

```text
┌──────────────┐
│ Sampling Rate│
│ 2.00 MHz     │
└──────────────┘

┌──────────────┐
│ Bandwidth    │
│ 410 kHz      │
└──────────────┘

┌──────────────┐
│ SNR          │
│ 14.7 dB      │
└──────────────┘

┌──────────────┐
│ Symbol Rate  │
│ 100 kSym/s   │
└──────────────┘
```

---

# 33. AI/ML page

Show the actual reasoning chain.

```text
PARAMETER IDENTIFICATION

Modulation
────────────────────────────
QPSK          █████████████ 92%
8PSK          █              5%
BPSK          █              3%

FEC
────────────────────────────
Convolutional ███████████    81%
LDPC          ██             14%
RS            █               5%

Interleaving
────────────────────────────
Block         ███████████    76%
Diagonal      ██             16%
None          █               8%
```

Then:

```text
Generated hypotheses: 3
```

---

# 34. Hypothesis page

This will be excellent for the judge explanation.

```text
HYPOTHESIS RANKING

┌─────────────────────────────────────────┐
│ H1                                      │
│ QPSK + Convolutional + Block            │
│ ML Score       0.57                     │
│ Recovery       PASS                     │
│ Validation     PASS                     │
│ Final Score    0.93                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ H2                                      │
│ QPSK + LDPC + Block                     │
│ Recovery       FAIL                     │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ H3                                      │
│ 8PSK + Convolutional + Block            │
│ Recovery       FAIL                     │
└─────────────────────────────────────────┘
```

---

# 35. Recovery page

Show:

```text
SIGNAL RECOVERY

Synchronization        PASS
Frequency correction   PASS
Timing recovery        PASS
Carrier recovery       PASS

Demodulation           QPSK
De-interleaving        Block
FEC                    Convolutional
Decoder                Viterbi

Recovery status        SUCCESS
```

---

# 36. Bitstream page

Show something like:

```text
RECOVERED BITSTREAM

1010101010101010
1101001010110010
0101001100101010
...

────────────────────────

Preamble
████████████████

Header
████████████████████████████

Payload
████████████████████████████████████
```

And:

```text
Total bits       12,480
Recovered bits   12,480
FEC corrections  137
Preamble         FOUND
Header           FOUND
```

---

# 37. The complete demo signal

I strongly recommend creating your **own known test signal**.

Generate:

```text
Random payload
      ↓
Known preamble
      ↓
Header
      ↓
Convolutional encoder
      ↓
Block interleaver
      ↓
QPSK
      ↓
AWGN
      ↓
Frequency offset
      ↓
Timing offset
      ↓
IQ file
```

Save:

```text
demo_qpsk_conv_block.iq
```

Then your application reads that file as if it were an unknown intercepted signal.

The application doesn't receive:

```text
"QPSK"
"convolutional"
"block"
```

as analysis input.

It receives only:

```text
IQ samples
```

The known ground truth is kept separately for testing.

---

# 38. You should create multiple test files

At minimum:

### Test 1 — clean

```text
QPSK
Conv
Block
SNR = 25 dB
```

Expected:

```text
PASS
```

### Test 2 — noisy

```text
QPSK
Conv
Block
SNR = 10 dB
```

Expected:

```text
PASS
```

### Test 3 — difficult

```text
QPSK
Conv
Block
SNR = 5 dB
frequency offset
timing offset
```

Expected:

```text
PASS / lower confidence
```

### Test 4 — different modulation

```text
8PSK
```

Expected:

```text
8PSK candidate
QPSK hypothesis fails
8PSK hypothesis succeeds
```

### Test 5 — unsupported signal

Generate something your MVP doesn't support.

Expected:

```text
UNCLASSIFIED
```

This is important because it proves your system doesn't blindly fabricate an answer.

---

# 39. Testing architecture

Create an automated test pipeline:

```text
GNU Radio Generator
       │
       ▼
Known Ground Truth
       │
       ▼
IQ/WAV
       │
       ▼
Your Application
       │
       ▼
Predicted Parameters
       │
       ▼
Compare with Ground Truth
```

Example:

```text
Ground Truth       Predicted

QPSK                QPSK       ✓
100 kSym/s          99.7 kSym/s ✓
10 dB SNR           10.4 dB     ✓
Conv FEC            Conv FEC    ✓
Block interleave    Block       ✓
```

---

# 40. Metrics you should show

For ML:

```text
Accuracy
Precision
Recall
F1-score
Confusion Matrix
```

For parameter estimation:

```text
MAE
RMSE
```

For recovery:

```text
BER
FER
FEC success rate
Preamble detection rate
```

For the complete system:

```text
End-to-end recovery success rate
```

---

# 41. Example MVP benchmark

Suppose you generate:

```text
1,000 test signals
```

You can report:

```text
Modulation classification accuracy: 94.2%

Symbol-rate MAE: 2.8%

Average BER after FEC: 1.2 × 10⁻⁴

End-to-end recovery success: 91.7%

Preamble detection: 96.3%
```

**Only report numbers you actually measure.**

Never manufacture these numbers for the presentation.

---

# 42. Where C++ fits

Your PS mentions C++.

Don't force C++ into every component.

Use it where performance actually matters:

```text
C# GUI
   │
Python orchestration
   │
Python DSP
   │
C++ optimized kernels
```

Potential future C++ components:

```text
large FFT processing
high-speed IQ parsing
real-time DSP
GPU acceleration
large-file processing
```

For the first MVP, Python + NumPy/SciPy is substantially faster to develop.

---

# 43. Where GNU Radio fits

GNU Radio should primarily be your:

```text
Signal generation
+
Testing
+
Synthetic dataset generation
```

Architecture:

```text
GNU Radio
    │
    ├── BPSK
    ├── QPSK
    ├── 8PSK
    ├── FSK
    ├── QAM
    │
    ├── FEC
    ├── Interleaving
    ├── Noise
    ├── Frequency offset
    └── Timing offset
          │
          ▼
      IQ dataset
          │
          ▼
      ML training
```

---

# 44. ML training architecture

Keep training separate from inference.

```text
             OFFLINE TRAINING
                   
GNU Radio
    │
    ▼
Synthetic Dataset
    │
    ▼
Preprocessing
    │
    ▼
Feature Extraction
    │
    ▼
ML Training
    │
    ▼
model.onnx / model.pt
    │
    ▼
Saved Model
```

Then production:

```text
             RUNTIME

IQ/WAV
  │
  ▼
DSP
  │
  ▼
Features
  │
  ▼
Saved ML Model
  │
  ▼
Prediction
```

Do **not retrain the model every time the user uploads a file.**

---

# 45. Recommended ML approach for the MVP

I would build it in stages.

### Version 1

Use engineered DSP features + classical ML:

```text
Features
    ↓
Random Forest / XGBoost
    ↓
Modulation
```

This is much easier to debug.

### Version 2

Try:

```text
Spectrogram
   ↓
CNN
   ↓
Modulation
```

### Version 3

Try raw IQ:

```text
I/Q
 ↓
1D CNN
 ↓
Modulation
```

For SIH, **a reliable classifier is more valuable than a fancy neural network that you cannot explain or validate.**

---

# 46. What NOT to implement initially

Do not spend your first weeks on:

```text
All possible FEC codes
All possible modulation schemes
Real-time SDR capture
GPU optimization
Distributed processing
Cloud deployment
Complex protocol decoding
Encryption/decryption
Satellite communication
Huge databases
Large LLM agents
```

They don't directly improve your MVP demonstration.

---

# 47. MVP versus full architecture

Your presentation should explicitly distinguish:

```text
                 COMPLETE ARCHITECTURE

IQ/WAV
  ↓
DSP
  ↓
ML
  ↓
Hypothesis Engine
  ↓
Synchronization
  ↓
FSK / PSK / QAM
  ↓
Block / Conv / Diagonal / PR
  ↓
Conv / RS / Concatenated / LDPC
  ↓
Validation
  ↓
Correlation
  ↓
Report
```

versus:

```text
                  MVP

IQ/WAV
  ↓
DSP analysis
  ↓
QPSK identification
  ↓
Top-K hypotheses
  ↓
QPSK synchronization
  ↓
QPSK demodulation
  ↓
Block deinterleaving
  ↓
Convolutional FEC
  ↓
Viterbi
  ↓
Preamble correlation
  ↓
Bitstream
  ↓
Report
```

Then say:

> **“The MVP validates the complete end-to-end methodology on a controlled subset. The architecture is modular and can be extended to the remaining modulation, FEC and interleaving families specified in the problem statement.”**

That is the correct SIH positioning.

---

# 48. Recommended implementation order

Do **not** build the GUI first.

Build in this order:

### Phase 1 — Signal fundamentals

```text
IQ reader
WAV reader
↓
complex signal representation
↓
waveform
↓
FFT
↓
spectrogram
```

Goal:

> Upload a file and visualize it.

---

### Phase 2 — DSP parameters

Implement:

```text
SNR
bandwidth
frequency offset
symbol rate
```

Goal:

> Automatically extract signal characteristics.

---

### Phase 3 — QPSK recovery

Implement:

```text
synchronization
↓
QPSK demodulation
↓
bits
```

Goal:

> Recover bits from your synthetic QPSK signal.

---

### Phase 4 — FEC

Implement:

```text
convolutional encoding
↓
Viterbi decoding
```

Goal:

> Demonstrate error correction.

---

### Phase 5 — Interleaving

Implement:

```text
block interleaver
↓
de-interleaver
```

Goal:

> Demonstrate the full recovery chain.

---

### Phase 6 — Correlation

Implement:

```text
known preamble
↓
correlation
↓
frame boundary
```

Goal:

> Identify the beginning of a frame.

---

### Phase 7 — ML

Train:

```text
BPSK
QPSK
8PSK
FSK
QAM
```

Goal:

> Automatically identify modulation.

---

### Phase 8 — Hypothesis engine

Implement:

```text
ML probabilities
↓
Top-K
↓
candidate configurations
↓
recovery
↓
validation
```

Goal:

> Demonstrate automated decision-making.

---

### Phase 9 — Desktop application

Only now build:

```text
C# WPF
↓
Upload
↓
Analysis
↓
ML
↓
Recovery
↓
Report
```

---

# 49. Final end-to-end implementation

Your finished MVP should effectively execute:

```text
                    USER
                     │
                     ▼
              ┌─────────────┐
              │ Upload File │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Validation  │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ IQ/WAV      │
              │ Parser      │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Preprocess  │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Signal      │
              │ Detection   │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ DSP Feature │
              │ Extraction  │
              └──────┬──────┘
                     │
             ┌───────┴────────┐
             ▼                ▼
       DSP Parameters       ML Model
             │                │
             │         Modulation
             │         FEC candidates
             │         Interleaver
             │                │
             └───────┬────────┘
                     ▼
              ┌─────────────┐
              │ Hypothesis  │
              │ Engine      │
              └──────┬──────┘
                     │
                TOP 3
                     │
                     ▼
              ┌─────────────┐
              │ Sync        │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Demodulate  │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Deinterleave│
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Viterbi     │
              │ FEC         │
              └──────┬──────┘
                     ▼
              ┌─────────────┐
              │ Validation  │◄─────────┐
              └──────┬──────┘          │
                     │                  │
              ┌──────┴───────┐          │
              │              │          │
             PASS           FAIL        │
              │              │          │
              │          Next hypothesis
              │              │
              ▼              └──────────┘
        ┌─────────────┐
        │ Bitstream   │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Correlation │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Header /    │
        │ Payload     │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │ Final Report│
        └─────────────┘
```

## 50. What I would make your actual SIH demo

If you have limited time, target this exact demonstration:

```text
                    DEMO

        demo_qpsk.iq / demo_qpsk.wav
                       │
                       ▼
                 File validation
                       │
                       ▼
             Waveform + FFT + Waterfall
                       │
                       ▼
              Parameter extraction
                       │
                       ▼
              ML → QPSK = 92%
                       │
                       ▼
          H1: QPSK + Conv + Block
                       │
                       ▼
               Synchronization
                       │
                       ▼
                  QPSK Demod
                       │
                       ▼
               Block Deinterleave
                       │
                       ▼
                Viterbi Decoder
                       │
                       ▼
               Recovered Bitstream
                       │
                       ▼
              Preamble Correlation
                       │
                       ▼
                 Header detected
                       │
                       ▼
                 Payload detected
                       │
                       ▼
                 SUCCESS REPORT
```

That is a **real, demonstrable vertical slice** of PS 26147.

The important part is that every major block actually does something. A judge should be able to upload your sample file and watch the system move from **raw signal → analysis → automated identification → recovery → validated bits → report**.

For the next step, I would build this as a **concrete implementation specification**: exact Python packages, exact C#/.NET packages, module-by-module APIs, data structures/JSON schemas between C# and Python, GNU Radio flowgraph, dataset format, QPSK signal-generation procedure, ML training procedure, and the exact order in which you should code each file.
