# Risks, Limitations and Future Scope

## 18.1 Major risks

### Synthetic-to-real gap

Models trained only on synthetic signals may perform worse on real recordings.

Mitigation:

- diverse synthetic channel conditions
- held-out parameter combinations
- real-data validation
- continuous retraining when labeled data becomes available

### Combinatorial search

Many candidate combinations can become expensive.

Mitigation:

- Top-K ranking
- parameter constraints
- early rejection
- retry/time limits

### Synchronization complexity

Timing and carrier recovery are nontrivial.

Mitigation:

- use established algorithms
- implement one modulation path first
- test each synchronizer independently

### File-format ambiguity

Raw IQ has no universal metadata structure.

Mitigation:

- explicit input configuration
- metadata inspection
- clear unknown state

### False confidence

A classifier may be confident but wrong.

Mitigation:

- downstream validation
- calibrated confidence where possible
- explicit low-confidence state

## 18.2 Limitations

The system cannot guarantee:

- universal modulation recognition
- universal FEC recognition
- universal interleaver recognition
- successful recovery at arbitrary SNR
- exact sample-rate recovery without sufficient information
- protocol interpretation for unknown formats

## 18.3 Future scope

Potential extensions:

- broader modulation families
- automatic protocol fingerprinting
- more FEC families
- more interleaver models
- improved real-world training data
- online/continual learning
- GPU acceleration
- distributed processing
- multi-channel analysis
- richer signal-segmentation models

Future scope must remain separate from demonstrated functionality.
