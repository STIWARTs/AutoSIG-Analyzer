# Validation & Bitstream Correlation

## Purpose

This is the stage that decides whether a hypothesis is **accepted**, and it is what directly satisfies the PS's "bitstream correlation for identification of header and payload" requirement. Without it, the system would simply report whatever its top-ranked hypothesis produced, untested; with it, every accepted result is backed by measurable evidence that the demodulated bitstream actually contains the known frame structure.

## Method

Every synthetic signal used for training and demo purposes (see `07-data-generation.md`) has a known preamble or sync-word pattern embedded in it before the payload. For a real off-air recording, the same principle applies using whatever preamble/frame-sync pattern is expected for the signal family being tested — the PS's own wording anticipates this ("correlation of bit stream for identification of header and payload").

For each hypothesis's recovered bitstream (`backend/validation/correlation.py`):

1. Compute the cross-correlation between the recovered bit sequence and the expected 32-bit preamble pattern (±1 signaling, so correlation counts agreeing bits).
2. If the peak correlation exceeds the acceptance threshold (0.90 of the 32-bit length), mark the hypothesis as **PASS** — it is *accepted* — and use the position of that peak to split the bitstream into header and payload.
3. If no correlation peak clears the threshold, mark the hypothesis as **FAIL** and move to the next hypothesis in the ranked list.

## What This Proves — and What It Does Not

A PASS is deliberately narrow evidence, and the UI wording says so explicitly:

- **It proves:** the known preamble pattern was detected in the recovered bits above the correlation threshold. That is strong evidence the correct modulation hypothesis was chosen and that synchronization, demodulation, de-interleaving, and FEC decoding produced a structurally coherent frame — a wrong-modulation candidate essentially cannot manufacture the preamble.
- **It does not prove:** that every payload bit is correct. The validator examines only the 32-bit preamble; the payload bits that follow it are never compared against anything at this stage. A recovery can therefore pass validation and still contain payload errors, and (rarer, but observed) a payload can be perfectly recovered while validation fails because the frame *head* alone was corrupted.

This is measured fact on the labeled corpus, not hypothetical (`tools/corpus_payload_eval.py`, Step-3 offline evaluation): 6 IQ captures pass frame validation while their recovered payloads still contain bit errors, and `qpsk_002` recovers its payload 100% bit-exact yet fails frame validation (a corrupted preamble region, score 0.56). Payload correctness can only be established offline against ground truth — never by this validator.

## Why This Matters Anyway

This is the mechanism that makes AutoSIG's core narrative real rather than staged: an AI misclassification (say, guessing QPSK when the signal is actually BPSK) does not silently produce a wrong-but-confident-looking *accepted* result. It produces a bitstream in which the expected preamble is not detected, which the system visibly rejects before trying the next candidate. The H1-fails / H2-passes sequence shown in the UI and in the demo video is a direct, live consequence of this check, not a scripted animation. It is an acceptance gate on frame structure — not a per-bit guarantee, and the Recovery and Bitstream screens say exactly that.

## Output of This Stage

For the accepted hypothesis: the recovered bitstream, the header segment, the payload segment, and the correlation score that justified the split. This feeds directly into the Report (see `00-overview.md` architecture diagram, and `11-ui-flow.md` for how it is displayed).
