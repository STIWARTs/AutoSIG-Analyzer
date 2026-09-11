# 7. Hypothesis Generation and Iterative Recovery Engine

## 7.1 Why it exists

ML classification alone cannot prove that a signal configuration is correct.

The recovery engine tests candidates using real DSP decoding and validation.

## 7.2 Candidate representation

```text
Hypothesis
 ├── modulation
 ├── symbol_rate
 ├── samples_per_symbol
 ├── frequency_offset
 ├── FEC type
 ├── FEC parameters
 ├── interleaving type
 ├── interleaving parameters
 └── confidence
```

## 7.3 Candidate ranking

Combine:

- ML probability
- DSP consistency
- parameter plausibility
- decoder success
- validation metrics

Do not try every possible combination.

Recommended configurable defaults:

```text
TOP_K = 3
MAX_RETRIES_PER_HYPOTHESIS = 1 or 2
TIME_LIMIT_PER_HYPOTHESIS = configurable
```

## 7.4 Recovery pipeline

For each candidate:

```text
Candidate
 ↓
Synchronization
 ↓
Demodulation
 ↓
De-interleaving
 ↓
FEC decoding
 ↓
Validation
 ↓
Score
```

## 7.5 Validation signals

Possible evidence:

- CRC pass
- parity consistency
- FEC syndrome/check result
- decoder convergence
- BER against known test data
- preamble correlation
- frame structure consistency
- bit statistics

## 7.6 Candidate score

A conceptual score can be:

```text
Score =
  w1 * ML confidence
+ w2 * synchronization quality
+ w3 * decoder quality
+ w4 * correlation quality
+ w5 * frame consistency
```

Weights should be calibrated using controlled validation data.

Do not claim the score is a probability unless it has been statistically calibrated.

## 7.7 Failure handling

```text
Candidate 1
 ↓
Validation FAIL
 ↓
Candidate 2
 ↓
Validation FAIL
 ↓
Candidate 3
 ↓
Validation FAIL
 ↓
Retry limit reached
 ↓
LOW CONFIDENCE / UNCLASSIFIED
```

The system must never loop indefinitely.

## 7.8 Why Top-3

The candidate count is a runtime control.

Instead of:

```text
5 modulation × 4 FEC × 4 interleavers × many parameters
```

which can explode combinatorially, the ML stage ranks likely candidates and only the top few enter expensive recovery.

The number must remain configurable.
