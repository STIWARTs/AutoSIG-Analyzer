# Progress

## MVP

### Input
- [ ] IQ loads
- [ ] WAV loads
- [ ] malformed files rejected
- [ ] canonical representation works

### DSP
- [ ] waveform
- [ ] spectrum
- [ ] waterfall
- [ ] constellation
- [ ] SNR
- [ ] bandwidth
- [ ] symbol rate for supported signal
- [ ] frequency offset

### ML
- [ ] synthetic dataset
- [ ] train/validation/test split
- [ ] model metrics
- [ ] offline model loading
- [ ] confidence output

### Recovery
- [ ] QPSK synchronization
- [ ] QPSK demodulation
- [ ] block deinterleaving
- [ ] convolutional FEC
- [ ] Viterbi
- [ ] validation
- [ ] wrong-hypothesis rejection
- [ ] bounded all-fail path

### Correlation/report
- [ ] known-sequence correlation
- [ ] frame candidate
- [ ] PDF
- [ ] JSON
- [ ] CSV

### GUI
- [ ] file selection
- [ ] progress
- [ ] cancellation
- [ ] plots
- [ ] parameters
- [ ] hypotheses
- [ ] recovery status
- [ ] report export

## Extended

- [ ] FSK
- [ ] additional PSK
- [ ] QAM
- [ ] convolutional interleaving
- [ ] diagonal interleaving
- [ ] pseudo-random interleaving
- [ ] Reed-Solomon
- [ ] concatenated codes
- [ ] LDPC

An architecture box or placeholder does not count as implemented.

## Final acceptance

The application must successfully demonstrate:

```text
user selects IQ/WAV
→ system validates
→ DSP analyzes
→ ML ranks
→ Top-K candidate generated
→ recovery executed
→ validation proves/rejects candidate
→ bit correlation shown
→ final report generated
```
