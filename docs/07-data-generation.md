# Synthetic Dataset Generation

## Why Synthetic Data

The PS's own background note points out that off-air recordings from different sensors and locations have inconsistent parameters, which makes fine-grained analysis unreliable even for a human analyst. For a prototype whose entire value proposition is "we can prove our pipeline correctly identifies and recovers a signal," the only practical way to prove correctness within a hackathon timeline is to control the ground truth: generate signals where the modulation, interleaving, FEC, noise level, and frequency offset are all precisely known in advance, so every claim the demo makes can be checked against a known answer.

## Tooling

**GNU Radio** is used to generate the synthetic dataset, since it provides mature, tested blocks for modulation, interleaving, FEC encoding, channel noise, and frequency offset — building these from scratch would be reinventing well-established DSP for no benefit.

## What Gets Generated

For the MVP, a set of QPSK signals with block interleaving and convolutional FEC encoding, each with:

- A known embedded preamble/sync-word pattern (used later for validation correlation).
- A range of SNR levels (to make the ML classifier and the recovery chain robust to noise, not just clean signals).
- Small, randomized carrier frequency offsets (so the synchronization stage has real work to do, rather than assuming a perfectly centered signal).

Each generated signal is saved in **both** formats the PS requires:

- **`.iq`** — raw complex samples, paired with a **SigMF** metadata sidecar file (`.sigmf-meta`) recording the sample rate, center frequency, and datatype. SigMF is an existing open standard for exactly this purpose — describing an IQ recording's parameters in a portable, machine-readable way — and adopting it avoids the ambiguity that raw `.IQ` files otherwise have (a bare `.iq` file has no header, so without accompanying metadata its sample rate and format have to be assumed rather than known).
- **`.wav`** — a stereo WAV file, using the common SDR convention of storing the I channel on the left channel and the Q channel on the right channel, so the same synthetic signal is available in both formats the PS calls out.

## Role in the Project

This dataset serves three purposes simultaneously: it is the labeled training set for the modulation classifier (`03-modulation-classification.md`), it is the test set used to prove the recovery chain and validation stage work correctly (`05-recovery-chain.md`, `06-validation-correlation.md`), and it is the exact set of files used live in the demo video, so the story told in the video is provably consistent with what was actually built and tested.

## Output Location

Generated files are stored under `datasets/`, with the GNU Radio flowgraphs used to produce them stored under `gnuradio/` (see `10-project-structure.md`).
