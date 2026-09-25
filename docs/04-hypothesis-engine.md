# Hypothesis Engine (Top-K Ranking)

## Purpose

Real recordings do not arrive labeled with their modulation, interleaving, and FEC scheme — and even a well-trained classifier's top prediction can be wrong. Rather than committing to a single guess, the Hypothesis Engine generates a short, ranked list of full candidate configurations and lets the Recovery Chain actually test the most likely ones against real decoders. This directly addresses the PS's requirement to identify FEC and interleaving alongside modulation, and it is the core mechanism that makes the system's output trustworthy rather than merely predicted.

## How a Hypothesis Is Built

A hypothesis is defined by a combination of:

- **Modulation** — taken from the Modulation Classification stage's output.
- **Interleaving scheme** — from a fixed candidate list for the current stage (MVP: block only; Stage 2 adds convolutional, diagonal, pseudo-random).
- **FEC scheme** — from a fixed candidate list for the current stage (MVP: convolutional code with Viterbi decoding only; Stage 2 adds Reed-Solomon, concatenated codes, LDPC).

**Important scope note:** in the current MVP the interleaving and FEC candidate lists each contain exactly one entry, so those fields carry the *same fixed values* (Block interleaving, Convolutional/Viterbi FEC) on every hypothesis, and the Recovery Chain applies that single fixed configuration rather than reading it per hypothesis. **Modulation is the only genuinely hypothesized, varying dimension.** The UI and report present interleaving/FEC as a one-time "fixed recovery configuration (MVP scope)" note, never as per-hypothesis search results.

## Ranking

Each hypothesis is scored primarily by the modulation classifier's confidence for that modulation, optionally adjusted by simple DSP-derived heuristics where available (for example, a measured symbol rate consistent with a particular FEC code rate can raise or lower a candidate's plausibility). In the MVP, where interleaving/FEC are fixed, ranking is effectively by modulation confidence alone, e.g.:

```
H1: QPSK + Block Interleaving + Convolutional/Viterbi     0.71
H2: QPSK + Diagonal Interleaving + Convolutional/Viterbi  0.18
H3: BPSK + Block Interleaving + Convolutional/Viterbi     0.06
```

## Bounding the Search Space

The full cross-product of modulation × interleaving × FEC candidates grows quickly, and trying all of them in a live demo would be slow and would dilute the demo's clarity. Two bounds keep this manageable:

- **Top-K limit** — only the top K hypotheses (K = 2 or 3 for the MVP) are actually attempted by the Recovery Chain. Lower-ranked hypotheses are not tried.
- **Stage-scoped candidate lists** — the MVP's interleaving/FEC candidate lists are deliberately small (one option each, as noted above), so the "cross-product" collapses to the modulation classes only. The larger candidate lists (Stage 2) are only enabled once the MVP's core loop is proven to work end-to-end; only then do interleaving and FEC become true search dimensions that the Recovery Chain varies and tests.

## Output of This Stage

An ordered list of hypothesis objects, each specifying a modulation (the only varied dimension in the MVP) plus the fixed MVP interleaving/FEC configuration, passed one at a time (in rank order) into the Recovery Chain until one passes validation or the list is exhausted.
