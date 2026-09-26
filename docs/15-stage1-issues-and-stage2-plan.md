# Stage 1 — Known Issues, Corrections, and the Path to Stage 2

This document has two parts: **Part A** is an honest accounting of every issue found in Stage 1 through testing and code audits, what caused each one, how it was (or should be) corrected, and its current status. **Part B** is the concrete plan for building everything the PS requires that Stage 1 deliberately left out.

The point of writing this down explicitly is the same reason the rest of `docs/` exists: a team that can show exactly what it tested, what it found, and what it did about it is more credible to a technical reviewer than a team that only shows a working demo and hopes nobody asks how it was verified.

Status key: **DONE** = verified fixed, with evidence. **UNCONFIRMED** = a fix was specified/attempted but not verified with a fresh test pass before this document was written — verify before submission. **DEFERRED** = known, understood, intentionally left for Stage 2/3. **OPEN** = confirmed, by code inspection, to still have the original problem — not yet attempted.

*Document accurate as of the post-commit-`dc60674` session (CFO unification, BPSK phase-grid fix, dashboard-fallback fix, GNU Radio provenance fix across 64 `.sigmf-meta` files and six docs, headline validation-scope qualifiers). `_estimate_snr`/`_occupied_bandwidth`/`_estimate_symbol_rate` in `backend/dsp/analysis.py` remain byte-identical to the initial commit `db17be0` — confirmed via git history, not inference.*

---

## Part A — Issues Found, and Their Corrections

### A1. Two independent, disagreeing carrier-frequency-offset (CFO) estimators

**Found:** A full code audit discovered the Analysis screen's displayed CFO (accurate to well under 1 Hz, with a quality gate that refuses to answer when uncertain) and the Recovery Chain's actual synchronization CFO (a separate, ungated estimator, often wrong by ~100 Hz) were computed by two completely different, disconnected functions. The number shown on screen was not the number actually driving recovery.

**Correction:** The recovery-chain estimator (`backend/dsp/sync.py`) was refactored to call the same accurate, gated estimator used for display, with correct unit conversion (Hz → rad/sample) and the previously-discarded constant phase term retained as a phase correction.

**Verification done:** Corpus-wide before/after comparison confirmed the two estimates now agree, and an "oracle test" (feeding the *true* CFO from ground truth into recovery) showed the achievable improvement ceiling was small (~2 of 64 outcomes) — confirming the fix was worth doing for correctness/honesty, but that it was never going to be the dominant lever on pass rate.

**Status: DONE.**

---

### A2. Modulation-blind CFO estimation failed on QPSK at low SNR

**Found:** The original CFO estimator tried to guess modulation-agnostic spectral tricks, which worked inconsistently — particularly failing on QPSK below 0dB SNR, sometimes reporting wildly wrong values (1000+ Hz off) with high apparent confidence.

**Correction:** The estimator now takes the CNN classifier's modulation prediction as a hint, using the noise-optimal math (squaring for BPSK, fourth-power for QPSK) for that specific modulation, and refuses to answer (`UNAVAILABLE`) rather than report a value when its own confidence/concentration score is below a measured threshold.

**Status: DONE**, verified against the full 64-file synthetic corpus.

---

### A3. Three other displayed "measured parameters" don't measure what their labels claim

**Found:** A code audit found:
- **Estimated SNR** overstates true signal quality by roughly 2–12 dB — it's `percentile(PSD, 90) − percentile(PSD, 20)`, a spectral-spread statistic, not a real SNR calculation.
- **Occupied bandwidth** returns close to the full sample rate for almost every file — it's the span of everything above `percentile(PSD, 20) + 6dB`, which collapses to ≈ the full band once noise lifts the floor.
- **Estimated symbol rate** is usually just a scaled copy of the CFO value (≈4×CFO) — it's the strongest bin of the fourth-power spectrum above `fs/200`, which picks up the rotated-carrier line rather than a genuine symbol-rate line.

**Correction:** Not yet implemented. **Confirmed via git history** (`backend/dsp/analysis.py` has exactly two commits — the initial one and the Step-2 CFO-unification commit `dc60674`, whose diff touches only the shared CFO estimator import and the center-frequency/`absolute_frequency_available` logic): these three functions are byte-identical to the original, unaudited code. All three original symptoms stand exactly as originally found.

**Status: DEFERRED**, confirmed still fully open, not partially addressed. If time allows before submission, apply the same refuse-rather-than-lie confidence gate the CFO estimator already has (cheaper and safer than re-deriving each estimator) so these fields show `UNAVAILABLE` rather than a confidently wrong number.

---

### A4. FEC and interleaving were displayed as tested hypothesis dimensions, but aren't

**Found:** The Hypothesis Engine only ever varies modulation. `interleaving="Block"` and `fec="Convolutional / Viterbi"` are hardcoded string constants on every hypothesis, and the Recovery Chain never actually reads `hypothesis.interleaving` or `hypothesis.fec` — every hypothesis is decoded with the identical fixed configuration regardless of its label. The UI displayed these labels as if they were part of a genuine search, which overstated what the system does.

**Correction:** UI copy and documentation updated to describe interleaving/FEC as a **fixed MVP recovery configuration**, not a predicted or tested dimension — modulation is the only thing genuinely hypothesized.

**Status: DONE.** Verified in the running UI (screenshots) and the Report JSON, both the pass case and the all-fail case: a "Fixed recovery configuration (MVP scope)" panel appears on the Recovery screen, and the Report JSON carries a matching `fixed_recovery_configuration.note` field stating this explicitly.

---

### A5. BPSK phase-ambiguity search used the wrong candidate grid

**Found:** The phase-state search tried `{0°, 90°}` for BPSK, but BPSK's actual physical ambiguity is a 180° flip, not 90° — meaning the correct resolving state was never in the candidate set.

**Correction:** Fixed the BPSK grid to `{0°, 180°}`.

**Status: DONE.** Verified across two independent test files, both a pass and an all-fail case — BPSK phase state renders as `0°` or `180°` only, never `90°`/`270°`.

---

### A6. Validation fallback picked the wrong "best" attempt when nothing passed

**Found:** When no hypothesis passed Frame Validation, the code picked the *last-tried* (highest-ranked-number) attempt rather than the one with the actual best correlation score.

**Correction:** Select by best correlation score among all attempts, not by rank order.

**Status: DONE.** Verified via a real all-fail case (Hyp1 0.562, Hyp2 0.375) where the Dashboard correctly surfaced the higher score (0.562), not the last-tried one. Further verified at scale: 8 independent historical rows sharing the same 0.5625 score were fingerprinted (SHA-256 on both input samples and recovered bitstreams) and confirmed to be 8 genuinely distinct computations landing on the same value by design, not a caching bug — see A6a below.

#### A6a. Why 0.5625 recurs across many different failed files (investigated, not a bug)

A later spot-check found several different, unrelated files in Dashboard history sharing an identical `0.5625` correlation score for their best-failed-attempt. This was investigated and confirmed to be a **real statistical artifact, not a caching or storage bug**: the 32-bit PREAMBLE constant is a 16-bit word repeated twice, giving it a natural ~0.5 self-similarity that acts as a "lucky floor" for otherwise-random bitstreams. A simulation on random bit streams of the relevant lengths found the max-correlation score has a median of 0.44–0.50 and a 90th percentile of exactly 0.5625 — meaning 0.5625 is the noise floor's natural resting point, and the six affected files are all ones independently confirmed (NO LOCK or high hard-BER) to have near-random recovered bits. This also validates the PASS threshold's design: 0.90 requires 31-of-32 bits agreeing, far above this floor, so the threshold isn't being brushed by noise.

---

### A7. Bitstream screen displayed the wrong value for "Phase state"

**Found:** The Bitstream screen rendered the hypothesis's rank number where it should have shown the actual resolved carrier phase state from the recovery attempt.

**Correction:** Display the real value.

**Status: DONE.** Verified — Bitstream screen's phase state now matches the Recovery screen's actual resolved value for the accepted hypothesis.

---

### A8. `absolute_frequency_available` was computed but never shown, and its logic was wrong

**Found:** This flag — meant to distinguish "we know the real RF center frequency" from "this is just a relative baseband offset" — was computed but explicitly skipped by the UI renderer, *and* its definition was wrong (`True` whenever a center-frequency field merely existed, even when that value was the `0.0` placeholder every synthetic file ships with). The net effect: the "Center Frequency" field could imply an absolute RF frequency when it was actually always a relative baseband offset.

**Correction:** Fixed the definition (only `True` for a genuine nonzero RF anchor) and un-skipped it in the UI, showing a "(relative to baseband)" qualifier when `False`.

**Status: DONE.** Verified in the UI ("center frequency Hz (relative to baseband)") and the Report JSON (`"absolute_frequency_available": 0.0`).

---

### A9. Recovery-screen PASS badges asserted correctness they didn't test — Synchronization specifically

**Found:** "Synchronization PASS," "Demodulation PASS," "De-interleaving PASS," and "Viterbi FEC PASS" mean, precisely, "the function ran without raising an exception" — not "this step produced a correct result." Only Frame Validation is a genuine correctness test.

**Correction implemented — note the real mechanism, which differs from the originally proposed design:** Synchronization now shows a `WARN` badge with "NO LOCK — CFO estimate refused; continuing uncorrected" instead of an unconditional PASS. **This is not gated on the `timing_metric` lock-quality score originally proposed** — `timing_metric` is still computed and reported as a diagnostic but doesn't gate anything. The actual gate, confirmed by code inspection: `locked` starts `True` and flips to `False` on exactly one condition — the shared CFO estimator (`backend/dsp/carrier.py`) returning `None`, which itself happens when the fourth-power periodogram's peak fails to exceed 4× the surrounding band's mean power within `|f| < fs/8`. On refusal, frequency correction is skipped entirely (never silently zeroed) and recovery continues uncorrected, with Frame Validation remaining the final, real gate. Demodulation/De-interleaving/Viterbi PASS badges remain "no exception raised," unchanged — only Synchronization got this treatment.

**Status: DONE**, with the mechanism description corrected to match what was actually built (spectral-concentration gate on the CFO estimator, not a separate timing-lock score).

---

### A10. Frame Validation only proves preamble detection, not full payload correctness

---

### A9. Recovery-screen PASS badges asserted correctness they didn't test

**Found:** "Synchronization PASS," "Demodulation PASS," "De-interleaving PASS," and "Viterbi FEC PASS" currently mean, precisely, "the function ran without raising an exception" — not "this step produced a correct result." Only Frame Validation is a genuine correctness test. This makes a failed recovery look visually contradictory ("everything passed except the last check!") when the truth is "only the last check was ever a real test."

**Correction:** Partially addressed conceptually (the wording throughout `docs/` now describes PASS badges precisely as "no exception" rather than "correct"). A deeper fix — gating the Synchronization badge specifically on the already-computed `timing_metric` lock-quality score, so it reports genuine `LOCK`/`NO LOCK` — was designed but not implemented, deliberately, since it's cosmetic-adjacent rather than a correctness fix.

**Status: DEFERRED to Stage 2/3.** Low risk to leave as-is for the demo as long as the accompanying documentation/narration is precise about what each badge means (which it now is).

---

### A10. Frame Validation only proves preamble detection, not full payload correctness

**Found:** "✓ Validated Recovery" / "validated" language throughout the app implied the entire recovered bitstream was confirmed correct. In reality, validation only correlates a known 32-bit preamble pattern — it never compares the payload against ground truth. A deeper audit built a genuine payload-level ground-truth comparison (using the fact that the synthetic dataset's payload bits are exactly reproducible from its generation seed) and found the preamble-only check can PASS with real payload bit errors present, and can FAIL even when the payload happens to be perfectly recovered — because the two checks examine different, non-overlapping bit regions of the frame.

**Correction:** Replace "validated recovery" / "✓ Validated Recovery" wording everywhere (UI, README, `docs/06-validation-correlation.md`) with precise language: validation confirms the known preamble was detected above a correlation threshold, which is strong evidence the recovery chain ran coherently, but is not a claim that every payload bit is correct.

**Status: DONE.** Verified across the codebase (not just one screen): `app/pages/dashboard.py` now reads "recovery accepted (preamble detected)" / "no hypothesis passed preamble detection" / "no hypothesis accepted" — computed live at render time; `README.md` has zero remaining matches for "validated/validates"; `docs/06-validation-correlation.md` now says "acceptance requires detecting the known preamble" and includes an explicit "What This Proves — and What It Does Not" section; `docs/12-mvp-scope.md` and `app/streamlit_app.py`'s matching code comment were caught and fixed in this same pass ("validated or all-failed" → "preamble-confirmed or all-failed"). A repo-wide grep after the fix found only one remaining "validat" hit, in a file-picker extension-validation code comment — semantically unrelated to recovery claims. Additionally, both `bitstream.py` and `recovery.py` now carry the scope qualifier directly under their headline text (not just in smaller supporting captions), so the limitation is visible at a glance, not two paragraphs down.

*(Note: if a screenshot still shows old wording like "validated recovery (from history)," that's a stale running Streamlit process showing a cached module from before this fix — restart the app to see current text.)*

---

### A11. Dataset metadata and documentation falsely claimed "GNU Radio generated"

**Found:** GNU Radio was never actually installed/runnable in the build environment. Every synthetic file was produced by a NumPy fallback generator (a correct, physically equivalent implementation — rectangular pulse shaping, a carrier rotator, AWGN noise — just not literally GNU Radio's code). The generator's own manifest honestly records this (`"generator": "NumPy flowgraph-equivalent fallback (GNU Radio unavailable)"`), but the `.sigmf-meta` files, README, and six documentation files all still claimed "GNU Radio generated."

**Correction:** All 64 `.sigmf-meta` sidecars patched (description field only — a per-file JSON-equality assertion confirmed no other field changed, and no `.iq`/`.wav`/`manifest.json` byte was touched). The root cause was fixed too, not just the output: `training/generate_dataset.py`'s `_write_sigmf` previously hardcoded the GNU Radio claim even on the fallback branch — it now writes whatever `run_flowgraph()` actually returns, so future regenerations self-describe correctly on either branch. `docs/07-data-generation.md`, `docs/03-modulation-classification.md`, `docs/model-training.md`, `docs/README.md`, `docs/10-project-structure.md`, `docs/12-mvp-scope.md`, `docs/02-dsp-pipeline.md`, `gnuradio/README.md`, and the top-level `README.md` all corrected.

**Status: DONE.** Verified via repo-wide grep for the claim pattern (0 matches outside `.conda`) and a 64/64 per-file description-vs-manifest agreement check. One residual known inaccuracy caught in this pass and pending: `docs/07-data-generation.md`'s "What Gets Generated" section says "a set of QPSK signals" when the corpus is actually QPSK+BPSK — flagged, small fix, apply before submission.

---

### A12. Low-SNR recovery failures are expected physics, not a defect — but weren't documented as such

**Found:** A rigorous failure-forensics audit (tracing all 27 imperfect recoveries in the 64-file corpus back to their root cause) found: 12 QPSK failures at ≤0dB SNR are the CFO estimator *correctly* refusing to lock (there genuinely isn't enough signal above the noise floor to reliably measure); 11 BPSK failures at the same SNR range are the error-correcting code being pushed past its correction capacity by channel noise, also expected; only 3 failures traced to a genuine estimator inaccuracy on individual files, and 1 to an unresolved edge case. Zero failures were traced to defects in the FEC decoder, de-interleaver, or alignment logic — those all behaved correctly in every traced case. An oracle test (feeding recovery the true, perfect CFO) confirmed this: pass rate barely moved, proving low SNR — not estimator quality — is the real ceiling.

**Correction:** This isn't a bug to fix — it's a finding to document honestly. `docs/12-mvp-scope.md` should state plainly that recovery is reliable at SNR ≥ 4dB, and that below that, the system correctly reports low confidence (refuses to lock, or shows a real but elevated bit-error-rate) rather than fabricating a clean result — matching how any real receiver behaves at the edge of physically recoverable signal.

**Status: OPEN — confirmed missing, not yet attempted.** Checked directly: `docs/12-mvp-scope.md` contains no SNR-dependent operating-envelope statement anywhere. The closest existing line ("Noise and signal impairments → Train and test across multiple SNR levels and frequency offsets") is a training-strategy note, not a confidence caveat, and doesn't say the same thing. Recommended exact addition, as a new Stage 1 bullet: *"Recovery confidence is SNR-dependent: synchronization and preamble-confirmed acceptance are reliable at ≈ +4 dB and above; below that the system frequently reports NO LOCK / no-acceptance — by design, rather than guessing."* This is a docs-only change — no logic or metrics need to move.

---

### A13. UI/design issues from earlier QA rounds

A series of UI-layer issues were found and fixed across several rounds of testing: a crash in the CNN-confidence panel (TypedDict incompatibility, fixed by switching to native Plotly), a blocker preventing `.sigmf-meta` files from uploading at all (browser MIME-type rejection, fixed), Plotly deprecation warnings, Streamlit's default alert/code-block styling fighting the app's custom flat design system (fixed via targeted CSS overrides), stale/contradictory Dashboard copy, and a missing post-synchronization constellation view (added, and verified to show 4 tight clusters for QPSK where the pre-sync view correctly shows a diffuse ring).

**Status: DONE**, verified via screenshot-based QA at each stage.

---

## Part B — Completing Stage 2 (per the PS's full requirements)

The PS requires demodulation of **PSK, QAM, and FSK**; de-interleaving of **Block, Convolutional, Diagonal, and Pseudo-Random**; and FEC via **convolutional/Viterbi, Reed-Solomon, concatenated codes, and LDPC**. Stage 1 covers PSK (QPSK+BPSK), Block interleaving, and convolutional/Viterbi only. Everything below is what remains, and how it plugs into the existing architecture without a redesign.

### B1. Additional modulations

- **QAM (16-QAM, 64-QAM, etc.):** extend `backend/ml/classifier.py`'s training classes and `backend/recovery/chain.py`'s demodulation logic with a QAM symbol-decision function (amplitude *and* phase, not phase-only like PSK). Requires regenerating the synthetic dataset with QAM-modulated captures (`training/generate_dataset.py`).
- **FSK:** requires a genuinely different demodulator (frequency discriminator rather than phase-based decisions) and its own synchronization approach (frequency deviation detection, not a Costas-style carrier lock). This is the most structurally different addition — budget real time for it, not just a config change.
- **Additional PSK orders (8-PSK etc.):** cheapest addition — same demodulation pattern as QPSK, just a larger phase-decision grid.

### B2. Additional interleaving schemes

`backend/recovery/coding.py`'s `block_deinterleave` is currently the only implementation, and `hypothesis.interleaving` is defined but unused. To make this real:
- Implement `convolutional_deinterleave`, `diagonal_deinterleave` (helical), and `pseudo_random_deinterleave` (needs a shared, known PRNG seed/sequence between encoder and decoder — same pattern already used for the synthetic dataset's payload generation).
- Wire `run_recovery` to actually dispatch on `hypothesis.interleaving` instead of always calling the block version — this is the structural fix that makes interleaving a genuine hypothesis dimension instead of a fixed label.
- Extend `build_hypotheses` to generate candidates across interleaving options, not just modulation.

### B3. Additional FEC schemes

`backend/recovery/coding.py`'s Viterbi decoder is currently the only implementation, and like interleaving, `hypothesis.fec` is defined but unused.
- **Reed-Solomon:** a block code, structurally different from convolutional/Viterbi — likely worth a well-tested library rather than a hand-rolled implementation, given how easy it is to get Galois-field arithmetic subtly wrong.
- **Concatenated codes:** an outer RS code plus an inner convolutional code (the standard CCSDS/DVB pattern) — needs both B3's RS and the existing Viterbi decoder composed together.
- **LDPC:** iterative belief-propagation decoding — a genuinely different decoding paradigm from Viterbi's trellis search; budget the most implementation time here.
- Same wiring fix as interleaving: `run_recovery` needs to dispatch on `hypothesis.fec`, and `build_hypotheses` needs to generate candidates across FEC options.

### B4. Hypothesis engine and search-space scaling

Once B2 and B3 make interleaving/FEC real dimensions, the Top-K search space grows from "modulation only" to "modulation × interleaving × FEC" — a much larger cross-product. Revisit the Top-K bound and per-hypothesis timeout logic (`docs/04-hypothesis-engine.md`) so a full search doesn't become too slow for a live demo; likely needs the ML classifier or DSP-derived heuristics to narrow candidates before the recovery chain attempts them, rather than trying every combination.

### B5. Dataset and validation implications

- The synthetic dataset generator (`training/generate_dataset.py`) needs new capture families for every new modulation/interleaving/FEC combination added, each with correct embedded ground truth (extending the existing manifest schema).
- The payload-level ground-truth evaluator built during Stage 1's audit work (comparing recovered bits against the exactly-reproducible transmitted payload) should be extended to cover every new configuration as it's added — this is what actually proves a new scheme decodes correctly, rather than just "runs without crashing" (see A9).

### B6. Suggested build order

Given the PS weighs all four listed tasks equally but they're not equally costly to implement, a sensible order by cost/value:
1. Convolutional and diagonal interleaving (cheap, reuses existing infrastructure)
2. Additional PSK orders and basic QAM (moderate — reuses phase/amplitude decision patterns)
3. Reed-Solomon FEC (moderate, ideally via a tested library)
4. Pseudo-random interleaving (needs the shared-seed design decision)
5. Concatenated codes (composes RS + existing Viterbi)
6. FSK demodulation (structurally distinct — most effort)
7. LDPC (most implementation-heavy — different decoding paradigm entirely)

This order front-loads cheap, high-confidence wins and pushes the two genuinely hard additions (FSK, LDPC) to the end, so a partial Stage 2 effort still demonstrably covers most of the PS's breadth even if time runs out before all of it is done.
