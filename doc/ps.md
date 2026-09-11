![](https://www.sih.gov.in/img1/SIH-Logo.png)
![Slide One](https://www.sih.gov.in/img/problem-statement-bg.png)

### Problem Statements

| S.No. | Organization | Problem Statement Title | Category | PS Number | Submitted Idea(s) Count | Theme | Deadline for Idea Submission |
|-------|--------------|-------------------------|----------|-----------|--------------------------|-------|------------------------------|
| 147   | National Technical Research Organisation (NTRO) | Automated model for analysis of .IQ and .wav files along with signal parameter extraction | Software | SIH26147 | 0/500 | Space Technology | 30 September 2026 |

---

### Problem Statement Details

**Problem Statement ID:** 26147  
**Problem Statement Title:** Automated model for analysis of .IQ and .wav files along with signal parameter extraction  

#### Description
- **Background**  
  The raw data for analysis of signal collected off the air typically range from few Khz to Ghz bands. The analysis is being carried out manually to identify the signal parameters and the resultant data is then utilised for processing signals in the designated sensors. This data is often insufficient for fine grain analysis for parameter extraction such as modulation type, sampling rate, FEC, interleaving, etc. This creates a need for advanced data processing to extract the observation data.

- **Details**  
  The terrestrial signals received from various sources include data in HF, VHF and UHF bands. The raw data collected in the form of `.wav` or `.IQ` format retains the characteristics of the waveform. Since data points are recorded from different sensors and locations, parameters may vary, making analysis insufficient to identify fine details such as sampling rate, modulation type, interleaving, FEC, etc.  
  Advanced models such as GNU Radio, Python, and C++ can enhance parameter extraction capability. Training data containing both `.IQ` and `.wav` formats can be utilised for identifying signal parameters and deeper analysis. The expected solution should be able to demodulate signals.

#### GUI Model Features
1. Identify signal parameters (Sampling frequency, Modulation, FEC, Interleaving).  
2. Demodulate signals (FSK, QAM, PSK).  
3. Carry out de-interleaving (Block, Convolution, Diagonal, Pseudo Random).  
4. FEC (short-constrained convolution codes with Viterbi decoding, RS block codes, Concatenated codes, LDPC).  
5. Bit stream correlation.  

#### Expected Solution
The system should improve feature visibility of signals with the help of a GUI, enable automated signal analysis to identify spectral features (sampling frequency, constellation plot, waterfall in time-frequency domain), demodulate signals, carry out de-interleaving and error correction. The output can then be used to correlate bit streams for identification of header and payload.

---

**Organization:** National Technical Research Organisation (NTRO)  
**Department:** National Technical Research Organisation (NTRO)  
**Category:** Software  
**Theme:** Space Technology  
**YouTube Link:** —  
**Dataset Link:** —  
**Contact Info:** —
