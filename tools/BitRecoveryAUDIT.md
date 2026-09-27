This is a read-only design pass. Let me trace the exact recovery code path before designing anything — starting with the chain, which is the piece I haven't yet read end-to-end in this session.


Let me read the frozen sync path fully (I must understand exactly how many bits survive to demodulation and any offset/truncation it introduces) and the existing validation split, plus the test fixtures:


Let me read the test fixture and the report/bitstream consumers so the design accounts for what already exists:


I now have the full chain. Before writing the design, let me get runtime evidence for the alignment assumptions (lengths, offsets, how recovered bits map to the true frame) — read-only, on a few representative captures:


Filename guesses were off — let me pull real names from the manifest instead:


My sloppy line again — fixing the GT build:


I have complete runtime evidence now. Every alignment assumption is confirmed: on a clean 18 dB capture the recovered stream is exactly 192 bits, sync peak lands at index 0, correlation 1.000, with **0 frame errors and 0 payload errors**. Note also (a critical design finding): my probe keyed on `accepted`, but `run_recovery` can emit `recovered_bits` on attempts that were *not* accepted (e.g. `bpsk_023`, `qpsk_000` returned `accepted: False` yet are not necessarily bit-empty) — the evaluator must key on the true-modulation attempt, not on acceptance. No files were modified; all checks were in-memory.

Here is the read-only design.

---

# Step 3 Design — Closing the Payload-Ground-Truth Loop (no implementation)

## A. Current recovery stages — exact code path & bit representation

Generation side ([generate_dataset.py](file:///e:/Hackathon/SIH2026/main_version1/training/generate_dataset.py) `generate()` L60–64) and the shared codec ([coding.py](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/coding.py)):

| Stage | Function | Bits in → out | Length |
|---|---|---|---|
| payload | `rng.integers(0,2,128)` | — → payload | **128** |
| frame | `make_frame(payload)` (L74) | `PREAMBLE[0:32] + HEADER[32:64] + payload[64:192]` | **192** |
| coded | `convolutional_encode(frame, terminate=True)` (L15) | rate-½ K=7 + 6 tail → ×2 | **396** |
| interleaved | `block_interleave(encoded, rows=12)` (L60) | reshape(12,·).T | **396** |
| symbols | `qpsk_map`/`bpsk_map` → `run_flowgraph` repeat×8 | QPSK 198 / BPSK 396 sym | 1584 / 3168 samples |

Recovery side ([chain.py](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/chain.py) `run_recovery`, [pipeline.py](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py) `run_pipeline`):

| Stage in chain | Code | What it produces | Exposed to caller? |
|---|---|---|---|
| Synchronize | `synchronize_psk(samples, 8, mod)` L28 | `symbols` (`corrected[best_offset::8]`, L100) | only as `synchronized_symbols` after phase rotate (L64/73) |
| Demodulate (hard) | `demodulate(rotated)` L51 | 396 hard bits (QPSK) | **No** — discarded after Viterbi |
| De-interleave | `block_deinterleave(hard_bits)` L56 | 396 coded bits | **No** |
| Viterbi decode | `viterbi_decode(..., terminated=True)` L56 → decoded[:-6] | ~192 frame bits | **Yes** — `RecoveryAttempt.recovered_bits` (L73) |
| Frame validation | `validate_bitstream(recovered_bits)` pipeline L28 | `ValidationResult` with `header_bits=recovered[pk:pk+64]`, `payload_bits=recovered[pk+64:]` ([correlation.py L19–21](file:///e:/Hackathon/SIH2026/main_version1/backend/validation/correlation.py#L19-L21)) | Yes |

**Key finding:** only two bit-level surfaces reach the caller — `attempt.recovered_bits` (the de-interleaved, Viterbi-decoded **frame**, verified = 192 bits) and, downstream, `ValidationResult.payload_bits`. The demodulated/coded intermediate streams (L51/L56) are **not returned**, so coded-bit BER is not obtainable without a chain change (see G/H).

## B. Ground-truth source — how true payload/frame bits are reconstructed

Deterministically from committed code + seed, exactly mirroring `generate()`'s RNG consumption order:

1. `rng = np.random.default_rng(20260922)` (the seed is `generate()`'s default arg, L53).
2. Loop `for modulation in ("QPSK","BPSK"): for index in range(count_per_class=32):` — **in this exact order**.
3. Each iteration consumes **precisely two** RNG draws in sequence: `payload = rng.integers(0,2,128)` then (after the coding funcs, which consume nothing) `offset_hz = rng.uniform(-85,85)`. `snr_db` comes from the cycling tuple (L57/L65), consuming nothing.
4. `gt_frame = make_frame(gt_payload)`; `gt_coded = convolutional_encode(gt_frame, terminate=True)`; `gt_interleaved = block_interleave(gt_coded)`. Payload truth = `gt_frame[64:192]`.
5. Map truth→file by the same `stem` rule the generator uses (L67), or — safest — by matching `round(offset_hz)` and `snr_db` against `manifest.frequency_offset_hz`/`snr_db` (audit already proved 64/64 exact float match).

**Mandatory integrity gate (prevents all "probably used X" risk):** before trusting a reconstructed payload for file *c*, the evaluator re-runs `run_flowgraph(gt_symbols, …)` and asserts `np.array_equal(reproduced_iq, on_disk_iq)`. The audit confirmed this holds bit-for-bit (max abs diff 0.0). If a file fails this assert, the generator/seed drifted → **that file is excluded and flagged, never scored against a possibly-wrong payload.** This converts "the generator probably used these bits" into "verified ground truth for this exact file."

Chosen option: **A (deterministic reproduction), no manifest change, no regeneration** — smallest/safest for the demo. Option B (write payload hex into manifest) is rejected for this step because it forces a corpus regeneration or a manifest edit that is no longer backed by the generator that produced the shipped files.

## C. Proposed metrics — exact formulas

For capture *c* with true payload `P` (128 bits) and the true-modulation attempt's recovered frame `F`:

- `L_c` = payload bits actually compared (see alignment, D): `L_c = min(128, len(F) − pk − 64)`, floor 0.
- `E_c` = `Σ_{i<L_c} [ F[pk+64+i] ≠ P[i] ]` (Hamming over the aligned payload region).
- **Payload BER** (per capture) `= E_c / L_c` when `L_c > 0`; else `undefined` (blank, **not 0**).
- **Payload bit accuracy** `= 1 − BER`.
- **Payload length match** = `(len(F) − pk − 64 == 128)` boolean; recorded per capture.
- **Frame errors / accuracy** = same over `F[pk:pk+192]` vs `gt_frame` (reported separately and explicitly labeled as inflated by the 64 fixed sync bits — payload is the headline number).
- **Perfect payload recovery** = `E_c == 0 AND L_c == 128`.
- Corpus aggregates use **explicit denominators** (see F): micro BER `= ΣE_c / ΣL_c` over comparable captures; macro BER `= mean(BER_c)` over the same set; both reported so a few large-error files can't silently dominate.

These are labeled **"synthetic bit-exact recovery"**, kept terminologically separate from **"frame validation"** (preamble correlation ≥ 0.90). The existing preamble validator is **not replaced or modified**; payload accuracy is an additional, offline, per-capture measurement.

## D. Alignment strategy — matching safely, never blindly from index 0

Verified on the corpus: for a clean capture `pk = 0`, `len(F) = 192 = len(gt_frame)`, sync score 1.000. But the design still proves alignment rather than assumes it:

1. Anchor on the fixed 64-bit `SYNC = PREAMBLE+HEADER` (a known constant, coding.py L7–8) via `np.correlate` in ±1 space, exactly like the validator → `pk = argmax`. Expect `pk == 0` on this zero-timing-offset corpus; **flag** any `pk ≠ 0` or sync score < sanity floor as anomalous instead of silently comparing.
2. Payload truth lives at logical frame offset `[64:192]`; recovered payload at `[pk+64 : pk+192]`. Compare only the overlapping region → `L_c`.
3. **Phase/rotation is not an index offset:** the discrete search in chain.py L45–60 rotates by exact 90°/180° multiples, which permutes Gray labels but never shifts bit position — so alignment is purely the `pk` translation, no additional lag to search. A wrong-but-selected rotation shows up as genuine payload bit errors, which is the correct accounting.
4. **Truncation:** the chain drops a tail to satisfy the 12-row/even block (L52–55, surfaced as `"N tail bits dropped"` L67–68). If that cut reaches into the payload, `L_c < 128` → status `PARTIAL`, compared count reported, missing tail **not** scored as correct or incorrect.
5. **Like-for-like stage rule:** only compare a stage against its own generator-side twin (payload↔payload, frame↔frame, coded↔coded). Never compare a recovered frame against a coded sequence or vice versa.

## E. Failure semantics — record, never silently zero

Per capture, the evaluator first selects the **true-modulation attempt** `a` (`a.hypothesis.modulation == ground-truth label`), *not* `result.accepted`. Then:

| Condition | Status recorded | BER field | Counted in |
|---|---|---|---|
| True modulation never in hypotheses (`top_k` miss) | `NOT_ATTEMPTED` | undefined | coverage gap, **not** a recovery error |
| `a is None` / `a.recovered_bits is None` / chain raised (`a.error`) | `RECOVERY_FAILED` | undefined | denominator of attempted |
| NO LOCK sync (`sync.locked == False`) | normal status **plus** `low_confidence` flag (from step WARN) | computed if bits exist | flagged, not excluded |
| Frame did **not** pass 0.90 preamble validation but payload region still present | `NOT_VALIDATED` | **still computed** | shown beside validated count |
| `L_c == 0` after alignment | `NO_COMPARABLE_BITS` | undefined | denominator |
| `0 < L_c < 128` | `PARTIAL` | computed over `L_c` | flagged with compared count |
| `L_c == 128` | `FULL` | computed | headline BER |

Missing results are stored as `null` BER with a status string, so a `—`/failure is never averaged as 0% or 100%. This directly answers the "reused/zero-NONE" principle already established in Step 2 (no silent 0 Hz): here, no silent 0 BER.

## F. Corpus report design

A single offline pass over all 64 captures (IQ as primary; WAV reported separately because its GT payload is identical but the int16 round-trip makes it a distinct condition). Output:

```
Corpus: 64 captures
  attempted (true mod in hypotheses): A
  not attempted (classification gap): 64-A      <-- reported, not hidden
  produced decodable frame:            D
  full 128-bit payload comparable:     F
  partial / no-comparable / failed:    (breakdown)

Payload (headline):
  bits compared:      ΣL
  bit errors:         ΣE
  micro BER:          ΣE/ΣL
  mean per-file BER:  avg over F files
  perfect recoveries: count(E==0 & L==128) / A

Frame accuracy (secondary, sync-bits-inflated): ...
Frame-validation (preamble ≥ 0.90) accepted: ...  <-- shown separately from payload-perfect

By SNR:  -2 / 0 / 4 / 8 / 12 / 18 dB  → {N, compared bits, BER, perfect}
By modulation: BPSK / QPSK             → {N, compared bits, BER, perfect}
low-confidence (NO LOCK) subtotal:      ...
integrity gate: IQ-bit-identity verified for X/64 (Y excluded)
```

The report deliberately prints **both** "validated" and "payload-perfect" counts side by side so the reader sees they are different quantities — that distinction is the whole point of Step 3.

## G. Files that would need modification (listed only — NOT touched)

New, production-isolated:
- `tools/corpus_payload_eval.py` — offline driver (loads manifest, reconstructs GT, runs `run_pipeline` per capture, computes/aggregates, prints/writes JSON). Preferred home so the shipped app is untouched.
- *(optional)* `backend/eval/ground_truth.py` — tiny pure module reproducing payload/frame/coded truth + the IQ-identity assert, so the test and tool share one implementation.
- *(optional)* `tools/corpus_payload_report.json` — saved output artifact (like the Step-2 `cfo_ab_*.json`).
- *(optional)* `tests/test_payload_eval.py` — asserts the reproduction+alignment harness is bit-exact on a known-good high-SNR capture.

Explicitly **unchanged** (Step 2 frozen + production pipeline): `backend/dsp/carrier.py`, `backend/dsp/sync.py`, `backend/dsp/analysis.py`, `backend/recovery/chain.py`, `backend/recovery/coding.py`, `backend/validation/correlation.py`, `backend/pipeline.py`, `datasets/*`, `manifest.json`, all `app/` UI, `widgets.py`.

**Only if** coded-bit / de-interleaved-stage BER is later demanded: `chain.py` would need to retain the L51/L56 intermediates and `RecoveryAttempt` (types.py) gain a field — that *does* touch the recovery return surface, so it is out of scope for the "keep production unchanged" preference and should be deferred.

## H. Risks / limitations (what could mislead)

1. **Reproduction drift** — GT is only correct if seed `20260922`, `count_per_class=32`, the `(QPSK,BPSK)×range(32)` order, the payload-then-offset draw sequence, and the codec constants are unchanged. The **IQ-bit-identity assert (§B step 5)** is the safety net; without it a generator edit would silently yield wrong "truth." Files failing the assert must be excluded, not scored.
2. **Reused noise realization** — `run_flowgraph` uses fixed `default_rng(42/43)` per call, so all 64 captures share one noise sequence. The by-SNR points are single-trial, correlated, **not** independent samples → error bars are not meaningful and curves can look spuriously smooth/consistent.
3. **Tiny per-file sample** — payload is only 128 bits; BER granularity is 1/128 ≈ 0.78%. Aggregate over ~40 decodable files is still small; present counts (ΣL, ΣE) alongside every ratio.
4. **Frame-accuracy inflation** — 64 of the 192 frame bits are the fixed sync pattern; "frame accuracy" will overstate performance. Payload is the honest headline; label frame metrics as sync-inclusive.
5. **`top_k` coverage gap** — if the classifier never proposes the true modulation, recovery BER is `NOT_ATTEMPTED`; counting that as high-BER (or as a miss-recovery) misattributes a *classification* failure to the *recovery* chain. Keep the two buckets separate.
6. **Alignment edge at −2 dB** — if the sync block itself is corrupted, `pk` may mis-anchor. Mitigation: require the expected `pk==0`/sanity score, else flag rather than compare.
7. **Acceptance vs true-modulation keying** — evaluating `result.accepted` (as my quick probe did) misses non-accepted attempts that still emitted bits, and can compare the wrong-modulation stream to the true payload. The evaluator must select by true modulation (§E) — getting this backwards would corrupt every number.
8. **WAV ≠ IQ condition** — different decoder path (int16, no center-frequency); keep its metrics in a separate table even though payload truth is shared.
9. **Scope of proof (§8):** these numbers demonstrate **internal pipeline self-consistency on a synthetic corpus** — AWGN + CFO only, rectangular pulses (no shaping), fixed 6000 baud, zero timing offset, zero initial-phase offset, fixed FEC/interleaving, one reused noise draw. They **do not** prove real-world accuracy, generalization to shaped/other-baud signals, multipath robustness, timing/phase recovery capability, or FEC coding gain. The report and any UI wording must carry that qualifier.

No code, manifest, corpus, UI, or Step 2 file was changed in this pass. Tell me if you want me to proceed to implement **G's tool-only plan** (production-isolated, Option A, with the IQ-identity integrity gate), or adjust the design first.