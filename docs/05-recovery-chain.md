# Recovery Chain

## Purpose

For a given hypothesis, actually attempt to recover the transmitted bitstream using real, deterministic DSP — no shortcuts or pre-canned outputs. This is the core technical proof of the project: it is the difference between "an AI thinks this is QPSK" and "we actually demodulated it as QPSK and got a bitstream out."

## Steps, in Order

### 1. Synchronization

Using the hypothesis's assumed modulation, lock a Costas loop (PSK/QAM) or frequency discriminator (FSK) onto the carrier, and run a symbol-timing recovery loop (Gardner or Mueller & Müller) to find the correct sampling instants. This step is modulation-specific, which is why it runs per-hypothesis rather than once globally.

### 2. Demodulation

Convert the synchronized complex samples into a raw symbol stream, then into raw bits, according to the hypothesis's modulation:

- **PSK/QPSK** — phase-based symbol decisions against the constellation. The MVP implements both QPSK (Gray-mapped I/Q quadrant decisions) and BPSK (real-axis sign decisions); the residual carrier phase ambiguity (90° for QPSK, 180° for BPSK) is resolved by testing each candidate rotation against the known sync word.
- **QAM** — joint amplitude/phase symbol decisions.
- **FSK** — frequency-based symbol decisions.

MVP scope implements QPSK and BPSK demodulation; QAM and FSK are Stage 2 (`12-mvp-scope.md`).

### 3. De-interleaving

Reverse the assumed interleaving scheme to restore the original bit/symbol ordering before FEC decoding:

- **Block de-interleaving** (MVP) — read the interleaved data into a matrix by columns, read it back out by rows (or vice versa, matching however the corresponding synthetic encoder wrote it).
- Convolutional, diagonal, and pseudo-random de-interleaving are Stage 2.

### 4. FEC Decoding

Attempt to correct errors and recover the original data bits:

- **Convolutional code with Viterbi decoding** (MVP) — the classic maximum-likelihood sequence decoder for convolutional codes; implementable directly or via an existing library (e.g. `commpy` or a hand-rolled trellis decoder).
- Reed-Solomon, concatenated codes, and LDPC are Stage 2.

## Output of This Stage

A candidate recovered bitstream (a sequence of bits), passed to Validation & Bitstream Correlation (`06-validation-correlation.md`) to determine whether this hypothesis's attempt should be accepted or rejected.

## Failure Handling

If any step in this chain cannot produce a usable output (for example, the Viterbi decoder's path metric never converges), the hypothesis is marked as failed immediately and the engine moves to the next hypothesis in the ranked list — there is no need to run validation on an attempt that has already clearly failed structurally.
