This is a read-only forensic pass. First, re-reading the frozen CFO estimator so my instrumented trace matches production exactly (evaluator code I wrote this session; chain/sync/coding/correlation are fresh in context):


One nuance handled: production `run_recovery` receives the DC-removed samples (`analysis.signal.samples`), so my trace applies `prepare_samples` identically. Running:


PowerShell mangled the inline f-strings — switching to the stdin-heredoc pattern:


The trace reproduces Step 3 exactly (ALL MATCH). The table is highly informative. Let me run targeted quantitative probes to separate MEASURED from LIKELY: CFO↔BER correlation, the NO_LOCK hard-BER effect, WAV quantization magnitude, qpsk_002 head-vs-payload split, and the PREAMBLE self-similarity:


Two more decisive probes to nail the CFO mechanism (phase-drift across the frame, not raw Δf) and confirm the alignment/timing story, then I have enough:


Almost complete. Final probe: the qpsk_026 anomaly (per-phase evidence), and the exact IQ↔WAV flip list:


Guessed the filename again — pulling it from the manifest and rewriting the probe cleanly:


One field-name mismatch to resolve in the Step 3 rows (Case A query returned empty) — checking the actual key encoding:


All evidence is in. Pulling the remaining per-row fields (true vs estimated CFO, anomaly flags) for the 27 imperfect captures to build the final table:


All evidence is collected and internally consistent (trace reproduced Step 3's 64/64 outcomes exactly; validator recomputation matches the 42/64 pass count exactly). Here is the forensic report.

---

# Step 4 — Failure Forensics Audit (READ-ONLY)

**Instrumentation used:** new [tools/failure_forensics.py](file:///e:/Hackathon/SIH2026/main_version1/tools/failure_forensics.py) → [tools/failure_forensics.json](file:///e:/Hackathon/SIH2026/main_version1/tools/failure_forensics.json). It re-walks the exact production path (same imports: `estimate_carrier_offset`, `synchronize_psk`, `chain._qpsk/_bpsk_demodulate` phase grid, `block_deinterleave`, `viterbi_decode`, `validate_bitstream`) and measures every intermediate against deterministic ground truth. **Cross-check: all 64 traced payloads match Step 3's report bit-for-bit (ALL MATCH).** No production file, evaluator, corpus, or Step-3 artifact was touched.

## 1. Recovery architecture & measurement points

```
IQ (complex64, 3168 samples) ─ prepare_samples (DC removal)
 └─ CFO: estimate_carrier_offset (8×-padded powered periodogram, ≥4× noise-floor gate)   [MEASURABLE]
 └─ sync: correct by exp(−j2π f̂ n/fs), pick timing offset 0..7 by (|I|−|Q|)² concentration [MEASURABLE]
 └─ symbol stream (sps=8 decimation)                                                     [MEASURABLE]
 └─ hard demod, 4-fold (QPSK) / 2-fold (BPSK) phase grid; candidate chosen by
    32-bit-preamble correlation of the DECODED output (threshold=−1)                      [MEASURABLE via replication]
 └─ tail trim to multiple of 12/even → block de-interleave (12 rows)                      [MEASURABLE]
 └─ Viterbi (K=7, 0o171/0o133, terminated) → 192-bit frame                                [MEASURABLE]
 └─ payload = frame[64:192] after Step-3 64-bit sync anchor                               [MEASURED by Step 3]
```

**Fact (MEASURED):** production does **not** expose hard bits, per-phase candidate scores, or deinterleaved coded bits — `RecoveryAttempt` only carries the final decoded frame. Forensics required replicating chain internals externally; that replication is bit-exact, so the gap is instrumentation-only, not behavioral.

## 2. Per-capture table — all 27 imperfect IQ captures

`hard` = raw symbol BER before FEC; `codedErr` = errors entering Viterbi (permutation-equal to hard); `pk` = Step-3 anchor offset; `comp` = comparable payload bits.

| capture | mod | SNR | CFO GT | CFO est | err Hz | NO_LOCK | val | outcome | pay BER | pk | comp | hard BER |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bpsk_000 | BPSK | −2 | −78.07 | −77.76 | +0.31 | no | FAIL | FULL | 0.078 | 0 | 128 | 0.134 |
| bpsk_006 | BPSK | −2 | +69.38 | +69.32 | −0.06 | no | PASS | FULL | 0.242 | 0 | 128 | 0.131 |
| bpsk_012 | BPSK | −2 | −62.59 | −62.48 | +0.11 | no | PASS | FULL | 0.148 | 0 | 128 | 0.116 |
| bpsk_018 | BPSK | −2 | +30.84 | +30.85 | +0.01 | no | PASS | FULL | 0.180 | 0 | 128 | 0.116 |
| bpsk_024 | BPSK | −2 | −44.23 | −43.84 | +0.40 | no | FAIL | FULL | 0.070 | 0 | 128 | 0.126 |
| bpsk_030 | BPSK | −2 | +62.38 | +62.34 | −0.04 | no | FAIL | PARTIAL | 0.500 | 96 | 32 | 0.124 |
| bpsk_001 | BPSK | 0 | +17.13 | +17.15 | +0.02 | no | PASS | FULL | 0.109 | 0 | 128 | 0.076 |
| bpsk_007 | BPSK | 0 | +42.27 | +42.14 | −0.13 | no | FAIL | FULL | 0.227 | 0 | 128 | 0.116 |
| bpsk_013 | BPSK | 0 | +51.99 | +51.77 | −0.22 | no | FAIL | FULL | 0.188 | 0 | 128 | 0.101 |
| bpsk_019 | BPSK | 0 | −58.07 | −58.09 | −0.02 | no | FAIL | FULL | 0.133 | 0 | 128 | 0.093 |
| bpsk_025 | BPSK | 0 | +1.25 | **+4.98** | **+3.73** | no | FAIL | FULL | 0.352 | 0 | 128 | 0.157 |
| bpsk_031 | BPSK | 0 | +68.29 | +68.23 | −0.06 | no | PASS | FULL | 0.031 | 0 | 128 | 0.068 |
| bpsk_026 | BPSK | +4 | +2.80 | **+5.68** | **+2.87** | no | PASS | FULL | 0.008 | 0 | 128 | 0.058 |
| bpsk_023 | BPSK | +18 | **−0.56** | **+5.05** | **+5.61** | no | FAIL | PARTIAL | 0.473 | 37 | 91 | 0.303 |
| qpsk_000 | QPSK | −2 | −74.13 | refused | – | **YES** | FAIL | PARTIAL | 0.478 | 13 | 115 | 0.487 |
| qpsk_006 | QPSK | −2 | −45.94 | refused | – | **YES** | FAIL | PARTIAL | 0.514 | 91 | 37 | 0.500 |
| qpsk_012 | QPSK | −2 | +78.80 | refused | – | **YES** | FAIL | PARTIAL | 0.519 | 51 | 77 | 0.533 |
| qpsk_018 | QPSK | −2 | −29.22 | refused | – | **YES** | FAIL | PARTIAL | 0.589 | 33 | 95 | 0.520 |
| qpsk_024 | QPSK | −2 | −48.53 | refused | – | **YES** | FAIL | PARTIAL | 0.525 | 48 | 80 | 0.485 |
| qpsk_030 | QPSK | −2 | +72.94 | refused | – | **YES** | FAIL | PARTIAL | 0.466 | 70 | 58 | 0.480 |
| qpsk_001 | QPSK | 0 | +78.62 | refused | – | **YES** | FAIL | PARTIAL | 0.532 | 81 | 47 | 0.515 |
| qpsk_007 | QPSK | 0 | −34.01 | refused | – | **YES** | FAIL | PARTIAL | 0.474 | 109 | 19 | 0.470 |
| qpsk_013 | QPSK | 0 | +66.56 | refused | – | **YES** | FAIL | PARTIAL | 0.500 | 84 | 44 | 0.503 |
| qpsk_019 | QPSK | 0 | +55.19 | refused | – | **YES** | FAIL | PARTIAL | 0.529 | 111 | 17 | 0.518 |
| qpsk_025 | QPSK | 0 | +46.44 | refused | – | **YES** | FAIL | PARTIAL | 0.400 | 103 | 25 | 0.467 |
| qpsk_031 | QPSK | 0 | −76.42 | refused | – | **YES** | FAIL | PARTIAL | 0.484 | 4 | 124 | 0.525 |
| qpsk_026 | QPSK | +4 | +10.08 | +9.81 | −0.28 | no | FAIL | PARTIAL | 0.517 | 41 | 87 | **0.523** |

Recovered length is 192 in every single case; `tailDrop=0` everywhere — so **no failure ever came from the chain's tail trimming** (MEASURED).

## 3. Failure categories (primary / secondary)

| # | captures | primary cause (evidence) |
|---|---|---|
| 1–12 | the 12 NO_LOCK QPSK @ −2/0 dB | **CFO_NOT_ESTIMATED → uncorrected rotation.** MEASURED: estimator refused (gate 4×), sync skipped correction, hard BER = 0.467–0.533 (≈channel-random *because of* the spin, not SNR alone — identical −2 dB BPSK runs at 0.12 with CFO −78 Hz corrected). Payload ≈0.5, FEC at capacity. Secondary: head garbage → anchor slid (pk 4–111) → PARTIAL truncation. |
| 13–23 | the 11 locked BPSK @ −2/0 dB with \|err\|<0.5 Hz (000,001,006,007,012,013,018,019,024,030,031) | **LOW_SNR_CHANNEL_BEYOND_FEC.** MEASURED: CFO correct (≤0.4 Hz), pk mostly 0, yet hard 0.068–0.134 → Viterbi removes most but leaves 3–31 payload errors. Classic hard-decision waterfall, no code defect visible. (bpsk_030 additionally has a head-corruption alignment collapse: pk=96, comp=32 — secondary PAYLOAD_ALIGNMENT.) |
| 24 | bpsk_025 (+0 dB) | **CFO_ESTIMATE_ERROR** (compound). MEASURED: est +4.98 vs +1.25 → 3.73 Hz residual → **89° phase drift** across the 3168-sample frame; hard 0.157 vs ≈0.09 typical at 0 dB. Secondary: LOW_SNR. |
| 25 | **bpsk_023 (+18 dB)** | **CFO_ESTIMATE_ERROR — the known Step-2 near-zero-CFO residual, now payload-confirmed.** MEASURED: GT −0.56 Hz, estimate +5.05; 5.61 Hz × 3168/48000 → **133° drift** — BPSK decision boundary is ±90°, so the back half of the frame is systematically mis-signed (hard 0.303 despite the cleanest noise in the corpus). Secondary: head corruption → pk=37 → PARTIAL. Not SNR, not FEC, not alignment: drift angle is sufficient to explain it. |
| 26 | bpsk_026 (+4 dB) | **CFO_ESTIMATE_ERROR (minor)** — 2.87 Hz → 68° drift, doubles hard errors (0.058 vs 0.020 at peers); FEC absorbs all but **1 payload bit** (BER 0.008). |
| 27 | **qpsk_026 (+4 dB)** | **DEMOD_PHASE_SELECTION failure — anomalous, see §10.** |

## 4. SNR breakdown (IQ, MEASURED from Step 3 + trace)

| SNR | n | perfect | non-perfect | micro-BER | NO_LOCK | anchor pk≠0 | val pass |
|---|---|---|---|---|---|---|---|
| −2 | 12 | 0 | 12 | 0.306 | 6 (all QPSK) | 10 | 3 |
| 0 | 12 | 0 | 12 | 0.257 | 6 (all QPSK) | 8 | 2 |
| +4 | 10 | 8 | 2 | 0.037 | 0 | 1 | 8 |
| +8 | 10 | 10 | 0 | 0.0 | 0 | 0 | 10 |
| +12 | 10 | 10 | 0 | 0.0 | 0 | 0 | 10 |
| +18 | 10 | 9 | 1 | 0.035 | 0 | 1 | 9 |

MEASURED: failures concentrate at ≤0 dB; every 0/−2 dB QPSK fails and every 0/−2 dB BPSK *locks and delivers a full 128-bit payload* (with errors). The +18 dB exception (bpsk_023) is CFO, not SNR. LIKELY: the pattern is SNR-correlated but **not** purely SNR-caused — it's the interaction of SNR with (a) the QPSK-only estimator refusal and (b) the FEC waterfall.

## 5. CFO correlation

- MEASURED: 46/52 locked captures estimate within ±0.5 Hz. Correlation of \|CFO err\| with payload BER across locked captures = **0.345** (weak) — because raw Δf is the wrong physical variable.
- MEASURED (better variable): residual **drift angle** = err × frame_len / fs × 360°:

| capture | SNR | err | drift | payload |
|---|---|---|---|---|
| qpsk_029 | +18 | 3.57 Hz | **42°** | PERFECT |
| bpsk_002 | +4 | 2.06 Hz | 49° | PERFECT |
| bpsk_014 | +4 | 2.81 Hz | 67° | PERFECT |
| bpsk_026 | +4 | 2.87 Hz | 68° | 1 bit |
| bpsk_025 | 0 | 3.73 Hz | **89°** | 0.352 |
| bpsk_023 | +18 | 5.61 Hz | **133°** | 0.473 |

MEASURED: monotone ordering — errors appear once drift approaches the ±90° BPSK / ±45°+FEC tolerance band and grow super-linearly beyond it. LIKELY: the true failure predictor is accumulated phase drift × SNR, not Δf alone; FEC fully hides drift <~70° at ≥+4 dB.
- The 12 refusals are **100% QPSK, 100% ≤0 dB**: gate operating range measured exactly (QPSK locks ≥4 dB, never ≤0 dB; BPSK locks at all six SNRs — the x² tone is stronger than x⁴).
- bpsk_023 reproduces the Step-2 documented near-zero-CFO estimator miss *independently* at the payload level. `carrier.py` untouched.

## 6. Alignment / synchronization

- MEASURED: every imperfect `recovered_len` = 192 and `tailDrop` = 0 → the PARTIAL statuses never came from the chain's trimming. PARTIAL = the Step-3 64-bit anchor slid off frame start (pk>0) because the recovered **head** is garbage, clipping the payload window (`pk+64+128 > 192`).
- MEASURED: pk≠0 occurs in exactly 15 captures, and *every one* is already destroyed upstream (NO_LOCK, bpsk_023, bpsk_030, qpsk_026). The one exception on (locked ∧ fine CFO ∧ ≥4 dB) is qpsk_026 — itself a phase-selection failure. **Alignment is never an independent cause; it's the downstream symptom.** No bits were shifted to improve BER anywhere in this audit.
- MEASURED: `timing_offset` ∈ 0–7 with no failure correlation (off=7: 10/16 perfect; off=0: 2/4). LIKELY reason: rectangular NRZ pulses make all 8 intra-symbol sample points equivalent, so the (|I|−|Q|)² concentration metric is flat and its argmax is decided by noise — harmless on this corpus, but it means **the timing stage is untestable on this corpus** (zero true timing offsets exist).

## 7. Demodulation & FEC stage where information is lost

Per-stage error counts (hard 396/790 → coded → payload 128) are in the table above. MEASURED, cleanly separated:

- **Errors enter at the channel, not at deinterleave**: coded-error count always equals hard-error count (deinterleave is a permutation) — the 12-row block interleave neither creates nor destroys errors on this corpus (no bursts to spread).
- **FEC gain measured as a waterfall**: ≤27/396 coded errors (≈6.8%) → **100% corrected** (qpsk_002/008/014/020: 27→0; bpsk_031: 27→4); ~50/396 (≈12.6%) → ~45–55% corrected, 9–31 residual (−2/0 dB BPSK); ≥120/396 (30%) → FEC collapses, output worse than useless (bpsk_023); ≈50% raw (NO_LOCK QPSK) → FEC at channel capacity, ~0.5 out. No evidence of Viterbi/deinterleave *implementation* defects anywhere (every recoverable error pattern was corrected exactly as expected for rate-½ K=7 hard-decision).
- **Viterbi leaves head residual**: in Case-B/A structures, surviving errors cluster at the frame head (first ~few decoded bits), consistent with trellis path-merging at the known-zero start state being under-constrained when preamble-region symbols are noisy (LIKELY; the terminated decoder should in principle be strongest there, so the exact head-concentration mechanism is marked LIKELY, not proven).
- Where errors first become visible: **at hard demodulation** in every single imperfect capture (all have elevated hard BER; none has clean hard bits that FEC then corrupted). MEASURED — no capture lost information at deinterleave or FEC *creation*; FEC only ever failed to correct, never injected.

## 8. Validation vs payload (Cases A & B)

**Case A — 6 IQ captures PASS validation with payload errors** (bpsk_001/006/012/018/026/031). MEASURED explanation: `validate_bitstream` correlates **only the 32-bit PREAMBLE**. Payload lives at bits 64–192 and is never examined. All six have intact preambles (score 1.00, pk 0) and corrupted payloads. Validator blind spot is structural, not a bug.
- Additional measured fragility: PREAMBLE = a 16-bit word repeated (`first16==last16: True`), giving it a 0.5 autocorrelation sidelobe at lag 16 — a half-aligned match reads as "50% valid".

**Case B — qpsk_002 PERFECT payload, validation FAIL.** MEASURED from the live pipeline object graph: true attempt's decoded frame is 192 bits; bits 64–192 (payload) match ground truth **exactly (0/128)**; the first ~7 of 64 sync bits are corrupted; validator score32 = 0.5625 (18/32) → FAIL; `accepted` = null (both attempts failed validation). The two metrics disagree because they **measure disjoint bit regions** — this is not a contradiction and not a corruption of our Step-3 result. LIKELY sub-cause of the corrupted head while the payload is perfect: surviving decoder residuals concentrated at the frame start (see §7 head pattern). Threshold/alignment/correlation logic itself behaved exactly as coded.

## 9. IQ vs WAV

- MEASURED: 23 captures have *any* BER difference between inputs; only 7 outcome-class flips; perfect count 37→38; micro-BER 0.0975→0.1047. Directionally random (bpsk_031 FULL 0.031→**PERFECT**; bpsk_000 FULL 0.078→PARTIAL 0.52; qpsk_026 PARTIAL→FULL 0.117).
- MEASURED impairment: the generator writes the WAV as `clip(complex*32767)` **without pre-normalizing**, so int16 conversion **clips noise peaks**: deviation from the float-IQ stream reaches ~2.8 amplitude units at −2 dB (symbol amplitude is 0.707) and ~0.5 even at +12 dB. So WAV is a genuinely clipped copy at every SNR — not merely 3e-5 quantization.
- LIKELY verdict: the flip pattern is chaotic sensitivity in the ≈0.5-BER / FEC-marginal regime (clipped samples move decision boundaries), not a systematic WAV-path defect. **No int16/stereo/normalization bug found** in `load_wav`; the honest fix target would be the *generator*'s missing headroom scaling, which is corpus data (frozen).
- No material difference in failure *categories*: the same three families (NO_LOCK QPSK, low-SNR BPSK, qpsk_026-type selection) dominate both inputs.

## 10. Failure matrix

| Category | Count (primary) | Captures |
|---|---|---|
| CFO_NOT_ESTIMATED (NO_LOCK refusal, ≤0 dB QPSK) | **12** | qpsk_000/001/006/007/012/013/018/019/024/025/030/031 |
| LOW_SNR channel errors beyond hard-decision FEC | **11** | bpsk_000/001/006/007/012/013/018/019/024/030/031 |
| CFO_ESTIMATE_ERROR (drift ≥68°) | **3** | bpsk_023 (known Step-2 residual), bpsk_025, bpsk_026 |
| DEMOD_PHASE_SELECTION | **1** | qpsk_026 |
| Alignment as independent primary cause | **0** | (15 pk≠0 cases all secondary symptoms) |
| FEC/deinterleave implementation defects | **0** | — |
| Validation-only discrepancies (not recovery failures) | 6 Case-A + 1 Case-B | validator scope issue, §8 |
| Unknown | 1 (qpsk_026 mechanism incomplete, see below) | |

Secondary factors logged per row in §2/§3: head-corruption→anchor slide (PARTIAL truncation, 15 cases), compound SNR+CFO (bpsk_025), clipping (WAV rows in the JSON).

**qpsk_026 — the one case not fully closed (UNKNOWN with partial evidence).** MEASURED: it locked with a good CFO estimate (−0.28 Hz) at +4 dB, yet the chain selected a quadrant rotation producing **207/396 hard errors while a 55-error candidate existed on the same symbol stream** (I swept all 8 timing offsets × 4 phases). LIKELY contributing: the offset-4 sampling point (best offsets 1/3/5 give ~27 errors, offset 4 gives 55 — realization luck) plus the phase-selection tiebreak being the 32-bit preamble correlation *after decoding*, which scored the wrong candidate 0.562 (vs healthy 1.00) — a weak-signal tiebreak, compounded by the preamble's lag-16 autocorrelation sidelobe. **UNKNOWN:** why exactly 55 errors at offsets {0,4} vs 27 at {1,2,3,5} for this realization; needs soft-metric instrumentation the current code doesn't expose. This is one capture; I refuse to name a root cause beyond what's measured.

## 11. Highest-value engineering issue (evidence-ranked, not chosen for plausibility)

Failure-budget of the 704 measured IQ payload errors: ~59% from the 12 NO_LOCK QPSK captures, ~17% from low-SNR BPSK (bpsk_000–031 family), ~14% from bpsk_023 alone, ~8% residual misc.

1. **Smallest technically justified change: make the QPSK CFO estimator usable ≤0 dB — not by lowering the 4× gate blindly, but because the refusal is *measurement*, not physics.** The captures at 0 dB have plenty of information (BPSK peers decode them with CFO corrected to 0.1 Hz). A coherently *longer*-integration or correlation-average estimate on x⁴ (still refused if genuinely below floor) addresses the single largest error pool (12 captures, ~420 errors) without touching thresholds that "make numbers look good" — it changes the *quality of the measurement*, gate semantics (null ≠ 0) preserved. Everything downstream (FEC) then works exactly as the waterfall in §7 predicts.
2. **Fix the proven CFO edge case bpsk_023** (near-zero-CFO miss, already known from Step 2, now payload-confirmed with a 133° drift mechanism): second-largest single-capture loss, well-localized, but it's one capture — *smaller* priority than (1) by measured budget.
3. **qpsk_026 phase-selection tiebreak**: only after understanding (10) is closed; the 32-bit-preamble tiebreak is demonstrably fragile, but changing it now would be tuning to one data point.
4. **No change warranted** for: the FEC/deinterleave (zero defects found), validation Case A/B (they are *correctly coded against their own narrow spec* — the honest response is documentation + Step-3 metric, already done), timing extraction (untestable on this corpus — fixing it would be unverifiable), the −2/0 dB BPSK residuals (**this is the low-SNR channel doing its job; 11 captures where the system behaves exactly as information theory predicts — leave them**), and the WAV clipping (frozen corpus property; documented, non-systematic).

## 12. Files NOT modified (verified `git status` before/after)

`backend/dsp/carrier.py`, `backend/dsp/sync.py`, `backend/dsp/analysis.py`, `backend/recovery/*`, `backend/validation/*`, `backend/pipeline.py`, `backend/eval/*` (Step-3 evaluator, byte-identical), `tools/corpus_payload_eval.py`, `tools/corpus_payload_report.json`, `tests/*`, `datasets/*` + `manifest.json`, `models/*`, `app/*`. **Only new files:** `tools/failure_forensics.py`, `tools/failure_forensics.json` (instrumentation output; the trace's 64/64 ALL-MATCH cross-check confirms Step-3 metrics are unchanged).