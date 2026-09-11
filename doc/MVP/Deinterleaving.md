# 10. De-interleaving and FEC

## 10.1 Why the order matters

A common recovery sequence is:

```text
Demodulated bits
 ↓
De-interleaving
 ↓
FEC decoding
```

The exact order depends on the actual signal chain and must be represented by the selected hypothesis.

## 10.2 Block de-interleaving

A block interleaver typically writes data into one arrangement and reads it out in another.

Recovery requires the correct:

- rows
- columns
- ordering
- depth/configuration

A wrong configuration produces apparently random data.

## 10.3 Convolutional de-interleaving

Requires the correct delay/depth structure.

Configuration must be part of the hypothesis.

## 10.4 Diagonal de-interleaving

Requires the correct diagonal traversal/permutation.

Again, type identification alone is insufficient; configuration parameters matter.

## 10.5 Pseudo-random de-interleaving

Requires a known or hypothesized permutation/sequence.

The system should not claim success without validation.

## 10.6 Convolutional FEC

For convolutional codes:

```text
soft/hard bits
 ↓
Viterbi decoder
 ↓
decoded bits
 ↓
validation
```

Important parameters can include:

- constraint length
- generator polynomials
- code rate
- termination
- puncturing

## 10.7 Reed-Solomon

RS decoding works on symbols rather than individual binary decisions.

Implementation must define:

- field
- code length
- message length
- symbol width
- error/erasure handling

## 10.8 LDPC

LDPC decoding may use iterative message passing.

Relevant metrics:

- iteration count
- parity-check/syndrome validity
- convergence

## 10.9 Concatenated codes

Represent as explicit stages.

Example:

```text
inner decoder
 ↓
deinterleaving if applicable
 ↓
outer decoder
 ↓
validation
```

The actual order must come from the hypothesis/configuration.

## 10.10 FEC validation

A decoder returning output does not automatically mean decoding succeeded.

Use:

- CRC
- parity/syndrome
- known sequence correlation
- frame consistency
- decoder metrics

## 10.11 MVP recommendation

Start with:

```text
QPSK
 ↓
soft/hard demodulation
 ↓
one block interleaver
 ↓
rate-1/2 convolutional code
 ↓
Viterbi
 ↓
CRC/known-sequence validation
```

Then expand to RS/LDPC and additional interleavers.
