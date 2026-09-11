## Core architecture

```text
.IQ / .WAV
   ↓
File Validation + Metadata
   ↓
Input Parsing / Normalization
   ↓
DSP Preprocessing
   ↓
Signal Detection + Segmentation
   ↓
DSP Analysis
   ├── FFT / Spectrum
   ├── STFT / Waterfall
   ├── Constellation
   ├── SNR
   ├── Bandwidth
   ├── Symbol Rate
   └── Frequency/Timing Features
   ↓
Feature Extraction
   ↓
AI/ML Inference
   ├── Modulation classification
   ├── FEC candidate
   └── Interleaving candidate
   ↓
Candidate Ranking
   ↓
Top-K Hypotheses
   ↓
Synchronization
   ↓
Demodulation
   ↓
De-interleaving
   ↓
FEC Decoding
   ↓
Validation + Confidence Score
   ├── Success → Best hypothesis
   └── Failure → Next candidate / bounded retry
                    ↓
             Low-confidence / Unclassified
   ↓
Bitstream Processing
   ↓
Bit Correlation / Header Detection
   ↓
Header / Payload Identification
   ↓
Final Report
```

# Complete System Architecture

## 4.1 Architectural layers

### Presentation layer

Desktop GUI:

- file selection
- analysis controls
- signal visualizations
- parameter dashboard
- candidate ranking
- bitstream viewer
- logs
- report export

### Orchestration layer

Controls:

- analysis job lifecycle
- pipeline stages
- candidate generation
- retries
- cancellation
- progress
- result aggregation

### Signal-processing layer

Contains:

- parsers
- preprocessing
- signal detection
- FFT/STFT
- parameter estimators
- synchronization
- demodulators
- de-interleavers
- FEC decoders

### AI/ML layer

Contains:

- dataset generation
- feature extraction
- training
- inference
- confidence scoring
- model/version management

### Validation layer

Contains:

- CRC/checks
- decoder metrics
- correlation
- frame consistency
- candidate score
- terminal status

### Persistence/reporting layer

Stores:

- input metadata
- extracted parameters
- model version
- candidate hypotheses
- processing steps
- metrics
- plots
- final results
