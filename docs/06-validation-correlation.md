# Validation & Bitstream Correlation

## Purpose

This is the stage that decides whether a hypothesis is accepted, and it is what directly satisfies the PS's "bitstream correlation for identification of header and payload" requirement. Without it, the system would simply report whatever its top-ranked hypothesis produced, correct or not; with it, every accepted result is backed by measurable evidence.

## Method

Every synthetic signal used for training and demo purposes (see `07-data-generation.md`) has a known preamble or sync-word pattern embedded in it before the payload. For a real off-air recording, the same principle applies using whatever preamble/frame-sync pattern is expected for the signal family being tested — the PS's own wording anticipates this ("correlation of bit stream for identification of header and payload").

For each hypothesis's recovered bitstream:

1. Compute the cross-correlation between the recovered bit sequence and the expected preamble pattern.
2. If the peak correlation exceeds a defined threshold, mark the hypothesis as **PASS**, and use the position of that peak to split the bitstream into header and payload.
3. If no correlation peak clears the threshold, mark the hypothesis as **FAIL** and move to the next hypothesis in the ranked list.

## Why This Matters More Than It Looks

This is the mechanism that makes AutoSIG's core narrative real rather than staged: an AI misclassification (say, guessing QPSK when the signal is actually BPSK) does not silently produce a wrong-but-confident-looking bitstream. It produces a bitstream that fails correlation, which the system visibly rejects before trying the next candidate. The H1-fails / H2-passes sequence shown in the UI and in the demo video is a direct, live consequence of this check, not a scripted animation.

## Output of This Stage

For the accepted hypothesis: the recovered bitstream, the header segment, the payload segment, and the correlation score. This feeds directly into the Report (see `00-overview.md` architecture diagram, and `11-ui-flow.md` for how it is displayed).
