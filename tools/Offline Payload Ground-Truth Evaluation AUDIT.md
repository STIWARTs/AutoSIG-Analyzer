I'll start by re-inspecting the current state of the repo (there's a new open file `BitRecoveryAUDIT.md` suggesting another session happened, and I must check whether any eval tooling already exists before writing anything).


Step 2 is committed; no eval tooling exists yet. Two new audit docs from other sessions — let me read them before touching anything:


The design from my Step 3 planning pass is confirmed intact. Let me quickly verify `GroundTruthAUDIT.md` is the forensic audit (no new surprises), then check the current test suite layout:


Now the reusable ground-truth module. It reuses the generator's actual functions/constants rather than duplicating, and the IQ-identity gate is the safety net against any RNG-order drift:


Now the pure scoring/alignment/metrics module — this is what the tests will exercise directly, decoupled from file I/O and the pipeline:


Now the offline evaluation driver:


Now the focused tests:


All 11 evaluator tests pass. Smoke run first, then the full corpus:


Working correctly — and honestly surfacing PARTIAL results with real bit errors at low SNR (exactly what the preamble-only validator never showed). Now the full corpus run:


The identity gate uses the system temp dir (outside the workspace) for the reproduction run — blocked by the sandbox. This needs to run outside it:


Full corpus done, all captures passed the integrity gate. Let me extract the breakdowns, verify reproducibility with a second run, and confirm no protected files changed:


Now verify the headline honesty point (validation-pass but payload-imperfect), reproducibility (second run hash), protected-files untouched, and the full suite:


Output got truncated by the shell. Let me run the three checks cleanly:


Decisive findings confirmed. Final full test suite run:


# Step 3 complete — payload ground-truth loop closed

## Files changed (all new, evaluation-only; nothing else touched)
- [backend/eval/__init__.py](file:///e:/Hackathon/SIH2026/main_version1/backend/eval/__init__.py) + [backend/eval/ground_truth.py](file:///e:/Hackathon/SIH2026/main_version1/backend/eval/ground_truth.py) — deterministic corpus replay (reuses the generator's own `qpsk_map`/`bpsk_map`/`run_flowgraph`/codec functions rather than duplicating constants) + the IQ bit-identity integrity gate.
- [backend/eval/payload_metrics.py](file:///e:/Hackathon/SIH2026/main_version1/backend/eval/payload_metrics.py) — pure alignment/BER/aggregate logic (no I/O, unit-testable).
- [tools/corpus_payload_eval.py](file:///e:/Hackathon/SIH2026/main_version1/tools/corpus_payload_eval.py) — the offline driver; runs the **unchanged** `run_pipeline`, selects the **true-modulation attempt (never `accepted`)**, emits JSON + summary, carries the interpretation-limits block in the report itself.
- [tests/test_payload_eval.py](file:///e:/Hackathon/SIH2026/main_version1/tests/test_payload_eval.py) — 11 tests: deterministic replay, length/sync-structure, manifest agreement, identity gate on real captures, PERFECT/FULL/PARTIAL/None/short semantics, shifted-alignment detection, aggregate-never-zeros-failures.
- `tools/corpus_payload_report.json` — generated output (no hardcoded metrics).

**Verified via `git status`:** zero modifications to `backend/dsp/carrier.py`, `sync.py`, `analysis.py`, recovery, validation, pipeline, `datasets/`, `manifest.json`, UI, or model. Step 2 stands.

## Tests run
`pytest tests -q` → **12 passed** (1 pre-existing + 11 new).

## Evaluation command
`python tools/corpus_payload_eval.py` — ran twice; report files **sha256-identical** (deterministic).

## Corpus integrity result
**64/64 IQ captures bit-identical to replayed ground truth** (max abs diff 0.0), 0 GROUND_TRUTH_MISMATCH. Every scored payload comparison is proven against the actual transmitted bits of that exact file.

## Aggregate payload BER (the number the loop never had before)
| | IQ | WAV |
|---|---|---|
| Micro BER (ΣE/ΣL) | **0.0975** (704/7220) | 0.1047 (780/7453) |
| Macro BER (mean/file) | 0.1448 | 0.1322 |
| **Perfect payload recoveries** | **37/64** | **38/64** |
| Frame-validation passes *(different metric)* | 42 | 44 |

## Failure breakdown (IQ)
PERFECT 37 · FULL-with-errors 12 · PARTIAL 15 · NOT_ATTEMPTED **0** (classifier coverage was complete at top_k=2) · RECOVERY_FAILED 0 · NO_LOCK-flagged 12 · alignment anomalies flagged 22 (all low-SNR; flagged, never silently shifted). WAV adds 1 NO_COMPARABLE_BITS at −2 dB.

## By SNR / modulation (IQ: perfect/validated/micro-BER)
−2 dB: 0/3/0.306 · 0 dB: 0/2/0.257 · 4 dB: 8/8/0.037 · 8 dB: 10/10/0.0 · 12 dB: 10/10/0.0 · 18 dB: 9/9/0.035. BPSK BER 0.072 vs QPSK 0.129. The Step-2 residual (`bpsk_023` at 18 dB, near-zero-CFO estimator miss) now shows up independently as a payload error — consistent, expected, inherited.

## Unexpected findings (honest surprises)
1. **"Validated" ≠ "correct", empirically:** 6 IQ captures pass preamble frame-validation yet carry real payload errors (`bpsk_001/006/012/018/026/031` — the 0 dB BPSK band). The old loop would demo these as successes.
2. **The reverse also happens:** `qpsk_002` recovers its payload **100% bit-exact** while its frame validation reports FAIL — a false-negative the new metric exposes. (Worth a future look; I changed nothing to "fix" it.)
3. Payload-perfect is ~5 files *lower* than validation-pass — so the honest headline is 37/64 perfect payload recoveries, not 42.

## Interpretation limits (embedded in the report JSON, mandatory for any reuse)
This measures **internal synthetic-corpus recovery performance only**: AWGN+CFO, rectangular pulses, fixed 6000 baud, zero timing/initial-phase offsets, one FEC/interleaver, one reused noise realization. It does **not** establish real-world/off-air accuracy, timing or phase-recovery quality, FEC identification, multipath behavior, or generalization. The corpus remains NumPy-fallback-generated (not "GNU Radio generated"), and frame-validation PASS must never be phrased as "payload recovered."