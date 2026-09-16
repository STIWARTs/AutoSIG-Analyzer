# Automated IQ/WAV Signal Analyzer & Demodulator Engine

A modular Python-based signal analysis and demodulation platform designed to automatically process IQ and WAV signal files, analyze their spectral characteristics, estimate signal parameters, identify modulation schemes, demodulate digital signals, apply FEC/interleaving operations, detect synchronization preambles, and extract payload data.

---

##  Overview

The **Signal Analysis Engine** provides an end-to-end framework for analyzing digitally modulated communication signals.

The system accepts raw **IQ**, **DAT**, and **WAV** signal files and performs multiple stages of signal processing:

```text
Signal File
    ↓
File Loading & Normalization
    ↓
DSP Analysis
    ├── FFT / PSD
    ├── Spectrogram
    ├── SNR Estimation
    ├── Power Estimation
    └── RMS Estimation
    ↓
Automatic Modulation Classification
    ↓
Demodulation
    ├── BPSK
    ├── QPSK
    ├── 8PSK
    ├── 16QAM
    └── FSK
    ↓
Bitstream Generation
    ↓
De-interleaving
    ↓
Viterbi FEC Decoding
    ↓
Preamble Correlation
    ↓
Payload Extraction
    ↓
Binary / ASCII Output
```

The project is designed as a **modular receiver-side signal processing prototype** that can be extended with additional modulation schemes, synchronization algorithms, channel models, and machine-learning-based signal classification.

---

##  Key Features

### Signal Ingestion

* IQ signal loading
* WAV signal loading
* DAT file support
* Complex64 and Complex128 IQ formats
* Int16 and Float32 interleaved I/Q formats
* Stereo WAV I/Q interpretation
* Mono WAV analytic-signal conversion
* Automatic signal normalization

### DSP Analysis

* FFT-based frequency analysis
* Power Spectral Density estimation
* Spectrogram generation
* SNR estimation
* Average signal power
* RMS amplitude estimation
* Symbol/Baud rate estimation

### Automatic Modulation Classification

The engine currently supports:

* **BPSK**
* **QPSK**
* **8PSK**
* **16QAM**
* **FSK**

### Demodulation

* BPSK hard decision demodulation
* QPSK I/Q demodulation
* 8PSK phase-based demodulation
* 16QAM symbol quantization
* FSK frequency-based demodulation

### Error Correction & Interleaving

* Block de-interleaving
* Diagonal-style de-interleaving
* Hard-decision Viterbi decoding
* Reed-Solomon decoding support

### Synchronization & Payload Processing

* Known preamble detection
* Sliding-window bit correlation
* Hamming distance calculation
* Correlation confidence estimation
* Payload extraction
* Binary-to-byte conversion
* Binary-to-ASCII conversion

### Visualization

The graphical interface provides:

* FFT / PSD plot
* Constellation diagram
* Spectrogram / waterfall visualization
* Signal information console
* Detected modulation
* Estimated SNR
* Estimated baud rate
* Preamble location
* Correlation confidence
* Extracted payload

---

##  Project Architecture

```text
SignalAnalysisEngine/
│
├── data/
│   ├── sample_bpsk.iq
│   ├── sample_qpsk.wav
│   └── sample_fsk.iq
│
├── docs/
│   └── Project_Idea_Documentation.md
│
├── src/
│   ├── __init__.py
│   ├── signal_io.py
│   ├── dsp_engine.py
│   ├── modulation.py
│   ├── fec_interleave.py
│   ├── correlation.py
│   └── gui.py
│
├── generate_samples.py
├── main.py
├── requirements.txt
└── README.md
```

---

##  Module Description

### `src/signal_io.py`

Responsible for signal ingestion and preprocessing.

Main responsibilities:

* Load IQ files
* Load WAV files
* Load DAT files
* Convert raw samples into complex signals
* Normalize signal amplitude
* Handle different IQ data formats

---

### `src/dsp_engine.py`

Provides core digital signal processing operations.

Main functions include:

```text
compute_fft()
compute_spectrogram()
estimate_snr()
estimate_baud_rate()
estimate_power()
estimate_rms()
```

These functions provide the basic signal characteristics required by the later processing stages.

---

### `src/modulation.py`

Handles automatic modulation classification and demodulation.

Supported modulation schemes:

```text
BPSK
QPSK
8PSK
16QAM
FSK
```

The module analyzes signal amplitude, phase, and instantaneous-frequency characteristics before selecting a modulation type.

---

### `src/fec_interleave.py`

Provides error-correction and de-interleaving operations.

Implemented functionality:

```text
Block De-interleaving
        ↓
Diagonal De-interleaving
        ↓
Viterbi Decoding
        ↓
Reed-Solomon Decoding
```

The Viterbi decoder implements hard-decision decoding for a rate-1/2 convolutional code with constraint length 3.

---

### `src/correlation.py`

Responsible for synchronization and payload extraction.

Main operations:

```text
Known Preamble
      ↓
Sliding Window Search
      ↓
Bit Comparison
      ↓
Correlation Confidence
      ↓
Preamble Position
      ↓
Payload Extraction
```

The module also provides conversion utilities for binary data.

---

### `src/gui.py`

Provides the PyQt5-based graphical interface.

The GUI connects all processing modules into a single signal-analysis workflow.

---

### `generate_samples.py`

Generates synthetic test signals for development and validation.

Currently generates:

```text
sample_bpsk.iq
sample_qpsk.wav
sample_fsk.iq
```

The generated signals contain controlled modulation and additive Gaussian noise.

---

### `main.py`

Application entry point.

It launches the graphical interface:

```python
from src.gui import main

if __name__ == "__main__":
    main()
```

---

## 🛠️ Technology Stack

| Technology | Purpose                                    |
| ---------- | ------------------------------------------ |
| Python     | Core development                           |
| NumPy      | Numerical and signal processing operations |
| SciPy      | DSP, FFT, spectrogram and WAV processing   |
| PyQt5      | Graphical user interface                   |
| PyQtGraph  | Real-time signal visualization             |
| Reedsolo   | Reed-Solomon decoding                      |
| Matplotlib | Supporting visualization capability        |
| PyTorch    | Future machine-learning extensions         |

---

## ⚙️ Installation

### 1. Clone or download the project

Open a terminal and navigate to the project directory.

```bash
cd SignalAnalysisEngine
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

For Windows Git Bash:

```bash
source venv/Scripts/activate
```

For Windows Command Prompt:

```cmd
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

If Reed-Solomon support is required and is not already present:

```bash
pip install reedsolo
```

---

## ▶️ Running the Project

### Generate test signals

Run:

```bash
python generate_samples.py
```

This generates:

```text
data/sample_bpsk.iq
data/sample_qpsk.wav
data/sample_fsk.iq
```

### Launch the GUI

Run:

```bash
python main.py
```

The Signal Analyzer GUI will open.

---

## 🖥️ Using the Application

### Step 1 — Load Signal

Select:

```text
Load Signal File (.IQ / .WAV)
```

Choose an IQ, DAT, or WAV file.

For raw IQ files, select the appropriate format:

```text
complex64
complex128
int16
float32
```

---

### Step 2 — Execute Analysis

Click:

```text
Execute Full Analysis Pipeline
```

The system will process the signal automatically.

---

### Step 3 — Inspect Results

The GUI provides:

* Frequency spectrum
* Constellation diagram
* Spectrogram
* Average power
* RMS amplitude
* Estimated SNR
* Estimated baud rate
* Detected modulation
* Demodulated bit count
* Preamble index
* Correlation confidence
* Extracted payload

---

##  Signal Processing Pipeline

The receiver architecture can be represented as:

```text
                 ┌──────────────────┐
                 │   IQ / WAV File  │
                 └────────┬─────────┘
                          ↓
                 ┌──────────────────┐
                 │  Signal Loader   │
                 └────────┬─────────┘
                          ↓
              ┌────────────────────────┐
              │      DSP Analysis      │
              │ FFT / SNR / Spectrogram│
              └───────────┬────────────┘
                          ↓
              ┌────────────────────────┐
              │ Modulation Classifier  │
              └───────────┬────────────┘
                          ↓
              ┌────────────────────────┐
              │      Demodulator       │
              └───────────┬────────────┘
                          ↓
                    ┌───────────┐
                    │ Bitstream │
                    └─────┬─────┘
                          ↓
              ┌────────────────────────┐
              │   De-interleaving      │
              └───────────┬────────────┘
                          ↓
              ┌────────────────────────┐
              │    Viterbi FEC         │
              └───────────┬────────────┘
                          ↓
              ┌────────────────────────┐
              │  Preamble Correlation  │
              └───────────┬────────────┘
                          ↓
              ┌────────────────────────┐
              │   Payload Extraction   │
              └───────────┬────────────┘
                          ↓
                    ┌───────────┐
                    │  Output   │
                    └───────────┘
```

---

##  Test Signals

The project includes synthetic test signals for basic validation.

### BPSK

```text
File:
data/sample_bpsk.iq

Sampling Rate:
1 MHz

Symbol Rate:
50 kBaud

Samples/Symbol:
20
```

### QPSK

```text
File:
data/sample_qpsk.wav

Sampling Rate:
1 MHz

Symbol Rate:
50 kBaud

Samples/Symbol:
20
```

### FSK

```text
File:
data/sample_fsk.iq

Sampling Rate:
1 MHz

Symbol Rate:
50 kBaud

Frequency Deviation:
±25 kHz
```

Gaussian noise is added to the generated signals to provide a more realistic test environment.

---

##  Reed-Solomon Support

The project provides optional Reed-Solomon decoding using the `reedsolo` package.

Install with:

```bash
pip install reedsolo
```

The decoder operates on byte-oriented data and converts between bitstreams and bytes automatically.

For successful correction, the incoming signal must contain data encoded using a compatible Reed-Solomon configuration.

---

##  Current Limitations

This project is currently a **research/prototype-level signal analysis engine**.

The following areas can be further improved:

* Automatic modulation classification is heuristic-based.
* Baud-rate estimation can require calibration for noisy signals.
* Carrier-frequency and timing synchronization are simplified.
* Current demodulators use simplified decision logic.
* FEC decoding requires a compatible transmitter-side encoding scheme.
* Reed-Solomon decoding requires correctly formatted RS codewords.
* Synthetic test signals do not yet represent every possible real-world communication protocol.
* Spectrogram visualization currently focuses on signal representation rather than protocol-specific decoding.

---

## 🔮 Future Scope

Possible future improvements include:

### Advanced Synchronization

* Automatic carrier recovery
* Symbol timing recovery
* Costas loop
* Gardner timing recovery
* Frequency-offset estimation

### Advanced Modulation Recognition

* 32QAM
* 64QAM
* GMSK
* MSK
* OFDM
* ASK
* PAM

### Machine Learning

The architecture can be extended with machine-learning-based modulation recognition:

```text
IQ Samples
    ↓
Feature Extraction
    ↓
ML / Deep Learning Model
    ↓
Modulation Classification
    ↓
Demodulation
```

Possible models include:

* CNN
* LSTM
* Transformer
* Autoencoder

### Protocol Analysis

Future versions can include:

* Frame detection
* Header decoding
* Protocol identification
* Packet parsing
* CRC validation
* Automatic payload interpretation

### Real-Time SDR Integration

The engine can eventually be connected to software-defined radio hardware for live signal analysis.

Possible integration targets include:

* RTL-SDR
* HackRF
* USRP
* Airspy
* Other SDR-compatible devices

---

## 🎯 Project Objective

The primary objective of the project is to create a **modular and extensible signal intelligence framework** capable of transforming raw signal data into meaningful communication information.

The project combines:

```text
Digital Signal Processing
        +
Automatic Modulation Recognition
        +
Digital Demodulation
        +
Error Correction
        +
Synchronization
        +
Payload Extraction
        +
Signal Visualization
```

This modular architecture makes the system suitable for experimentation, academic research, communication-systems education, and future SDR/ML-based signal analysis applications.

---

## 👨‍💻 Development

The project follows a modular architecture so that individual components can be independently improved without redesigning the entire system.

```text
Signal I/O
    ↓
DSP
    ↓
Modulation
    ↓
Demodulation
    ↓
FEC
    ↓
Correlation
    ↓
Payload
    ↓
Visualization
```

---

##  License

This project is intended for educational, research, and experimental purposes.

A formal open-source license can be added based on the intended distribution model.

---

##  Project Status

**Current Status: Functional Prototype**

Implemented:

* Signal ingestion
* IQ/WAV processing
* FFT analysis
* Spectrogram
* SNR estimation
* Baud-rate estimation
* Modulation classification
* Demodulation
* De-interleaving
* Viterbi decoding
* Reed-Solomon support
* Preamble correlation
* Payload extraction
* PyQt5 graphical interface
* Synthetic signal generation

The project is structured for further development toward a complete automated SDR signal-analysis platform.
