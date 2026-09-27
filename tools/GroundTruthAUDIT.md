This is a read-only forensic pass. Let me map every source that could establish ground truth — generator code, manifest writer, and constants — before reading them in detail.


Found both candidate generators. Reading them in full, plus the shared constants they use:


The manifest's `generator` field already tells us which path ran. Now the frame/FEC/interleaving constants and the validator:


Now the validator and the ingestion parser (to see what metadata is actually read back), plus a repo-wide scan for other ground-truth stores:


The parser never reads the `autosig:*` annotations back — noted. Now the decisive empirical check (read-only): replay the generator's seeded RNG and compare against the actual corpus bytes:


Bit-for-bit reproduction confirmed. Now scanning for overstated claims and checking the classifier's eval path:


One last sweep for hidden ground-truth stores (yaml/csv/npz/pkl/parquet anywhere in the repo):


# Synthetic Corpus Ground-Truth Forensic Audit — investigation only, nothing modified

**Integrity statement:** no file, code, config, manifest, or corpus data was created, modified, or deleted in the project tree. The only writes were two temporary `.iq` replays under `%TEMP%` (outside the workspace), deleted immediately after comparison.

---

## 1. The actual generator(s)

| Role | File · function | Status |
|---|---|---|
| Active corpus generator | [generate_dataset.py](file:///e:/Hackathon/SIH2026/main_version1/training/generate_dataset.py) `generate()` (L53–79) | **This is what produced all 64 captures** |
| Waveform impairment stage | [synthetic_flowgraph.py](file:///e:/Hackathon/SIH2026/main_version1/gnuradio/synthetic_flowgraph.py) `run_flowgraph()` (L13–47) | Imported and called by `generate()` at L15–19, L69 |
| Manifest writer | `generate()` L73–78 | Writes exactly the 7 fields seen |
| Classifier training consumer | [train_classifier.py](file:///e:/Hackathon/SIH2026/main_version1/training/train_classifier.py) L33–37 | Reads manifest for labels/split |

**GNU Radio vs NumPy fallback — verdict:** the GNU Radio code path (L35–47) exists but **never executed for this corpus**. Empirical proof: the `generator` field of **64/64** manifest entries is `"NumPy flowgraph-equivalent fallback (GNU Radio unavailable)"` (returned at [synthetic_flowgraph.py L30](file:///e:/Hackathon/SIH2026/main_version1/gnuradio/synthetic_flowgraph.py#L30)). GNU Radio is not installed in `.conda` (import fails → fallback branch). Note the contradiction: each `.sigmf-meta` still says `"core:description": "GNU Radio generated QPSK; SNR -2.0 dB"` — **false for every file in the corpus** (see §10).

## 2. Complete trace of `qpsk_000_snr-2_cfo-74`

All parameters below are **internal to `generate()` at creation time**, in order:

1. `payload = rng.integers(0,2,128)` — 128 random bits from a **seeded** RNG, `np.random.default_rng(20260922)` (seed is a default arg, L53).
2. `frame = make_frame(payload)` → `PREAMBLE(32) + HEADER(32) + payload(128)` = **192 bits** ([coding.py L74–75](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/coding.py#L74-L75)).
3. `convolutional_encode(frame, terminate=True)` — rate-½, K=7, generators `(0o171, 0o133)`, 6 tail bits → **396 bits** (coding.py L15–24).
4. `block_interleave(encoded)` — 12-row block, write-rows/read-cols (coding.py L60–64) → 396 bits.
5. `qpsk_map(...)` — Gray map `1−2b₀`, `1−2(b₀⊕b₁)`, `/√2` (generate_dataset.py L25–29) → **198 symbols**.
6. `snr_db = snrs[index % 6] = −2.0` (cycling set L57); `offset_hz = rng.uniform(−85, 85) = −74.12669192031848`.
7. `run_flowgraph(...)`: `repeat ×8` → 1584 samples → rotator `×exp(+j2π·f·n/48000)` → AWGN with `σ = √(P_avg/(2·10^(SNR/10)))`, noise from **fixed** `default_rng(42)`/`default_rng(43)` → `tofile` as `cf32_le`.
8. Side outputs: `.sigmf-meta` (`core:frequency: 0.0` placeholder + `autosig:*` annotations), stereo int16 `.wav` from the same samples.

**Empirical confirmation (ran this pass, read-only):** replaying the seeded RNG reproduces all 64 manifest CFOs and SNRs with **0 mismatches**, and regenerating the waveform produces a file **bit-identical** to `qpsk_000_snr-2_cfo-74.iq` (max abs diff **0.0**, same for `bpsk_000`). The entire corpus is exactly reproducible from `generate()` + seed + the committed code.

## 3. Ground-truth parameter table

| Parameter | Known by generator? | Actually injected into waveform? | Recorded in manifest? | Stored elsewhere? | Usable as ground truth now? |
|---|---|---|---|---|---|
| Modulation | Yes (loop var) | Yes (symbol map choice) | Yes (`label`) + sigmf `core:label` | — | **Yes** |
| SNR (signal-power basis) | Yes | Yes (noise σ formula, fallback L26) | Yes (`snr_db`) + sigmf `autosig:snr_db` | — | **Yes** (definitional: symbol-power-based, not classic Eb/N0) |
| CFO / frequency offset | Yes | Yes (rotator arg, fallback L24) | Yes (`frequency_offset_hz`) + sigmf `autosig:frequency_offset_hz` | — | **Yes — verified, see §9** |
| Sample rate | Yes (`SAMPLE_RATE=48000`, L21) | Yes (rotator normalization) | Yes (`sample_rate`) + sigmf `core:sample_rate` | WAV header | **Yes** |
| Samples per symbol | Yes (`SAMPLES_PER_SYMBOL=8`, L22) | Yes (`np.repeat`) | **No** | Traceable only in code | **Yes (via code constant, not data)** |
| Symbol rate | Implied = fs/8 = 6000 baud | Yes (by repeat) | No | Code constant | **Yes, trivially (no independent variation — always 6000)** |
| Phase offset / carrier phase | Yes — **always 0** (rotator starts at phase 0; GR osc initial phase 0) | Only its absence | No | Code structure | **No in any meaningful sense: GT is constant 0 for all 64 files; phase recovery is never exercised** |
| Timing offset | Yes — **always 0** (repeat starts at sample 0, no delay channel) | Nothing injected | No | Code structure | **No: constant 0; a timing-recovery estimator has nothing to find** |
| FEC | Yes (`convolutional_encode`) | Yes | No | sigmf `autosig:fec` (string constant) | **Yes as scheme identity; not as per-file coding gain** |
| Interleaving | Yes (`block_interleave`, rows=12) | Yes | No | sigmf `autosig:interleaving` | **Yes as scheme identity** |
| Preamble | Yes (`PREAMBLE` constant, coding.py L7) | Yes (first 32 frame bits) | No | Code constant | **Yes** |
| Header | Yes (`HEADER`, coding.py L8) | Yes (bits 32–63) | No | Code constant | **Yes** |
| Payload bits | Yes (seeded RNG) | Yes | No | Reproducible from seed 20260922 | **Yes — reproduction verified bit-identical** |
| Full encoded/interleaved bit sequence | Yes | Yes | No | Reproducible | **Yes (same reproduction)** |
| Frame length | Yes (192→396→198/396 symbols→1584/3168 samples) | Yes | No (implied by file size) | Code | **Yes** |
| Pulse shaping / filter | Yes — **none** (rectangular `repeat`, no RRC filter anywhere) | Nothing injected | No | Code | **No as an evaluative dimension: constant "no shaping"; real-world shaped signals untested** |
| Noise realization | Yes — literally sample-by-sample (`default_rng(42)/(43)`, fallback L27–28) | Yes | No | Code | **Yes, fully reproducible. ⚠ Same noise sequence reused in all 64 files** |
| Multipath / fading / other channel impairments | Never modeled (`taps=[1.0+0j]`, `epsilon=1.0`) | No | — | — | **N/A — channel is AWGN+CFO only** |
| WAV quantization | Yes (int16 clip, L48–50) | Yes | No | — | Derivable, not recorded |

## 4. A/B/C/D distinction (the trap you flagged)

- **(A) Generator knows / (B) injected:** for CFO, SNR, modulation, payload, and noise, all four generation parameters are injected verbatim — proven by the bit-identical reproduction, not assumed.
- **(C) Manifest record:** manifest carries only 7 fields; `frequency_offset_hz`/`snr_db` are the same float objects passed to the impairment function (generate_dataset.py L66→L69→L74), not filename-derived and not re-estimated.
- **(D) Legitimate evaluation GT:** CFO, SNR, modulation, sample rate, and (via reproduction) the exact bit sequence and noise. **Constant-by-construction values (phase offset=0, timing offset=0, symbol rate=6000, no shaping, Block/Viterbi) are *not* evaluative ground truth** — a metric computed against a parameter that never varies measures nothing about the system's ability to estimate it.

## 5. Manifest-generation code — exactly what is written and why

[generate_dataset.py L73–75](file:///e:/Hackathon/SIH2026/main_version1/training/generate_dataset.py#L73-L75): `iq`, `wav` (filenames), `label` (loop modulation), `snr_db` (cycled set element), `frequency_offset_hz` (the RNG draw passed straight to `run_flowgraph`), `generator` (return string of `run_flowgraph`), `sample_rate` (module constant). Nothing else was available at that point in the authoring of the record — payload/frame/noise objects exist in scope but are deliberately not serialized. The filename embeds *rounded* copies (`snr{:+.0f}_cfo{:+.0f}`, L67); the manifest holds full precision.

## 6. Other ground-truth sources found

| Source | Contents | Independence |
|---|---|---|
| `*.sigmf-meta` annotations (64 files) | `core:label`, `autosig:snr_db`, `autosig:frequency_offset_hz`, `autosig:interleaving`, `autosig:fec` | **Copy of same variables, not independent.** Also `core:frequency: 0.0` placeholder (the reason `absolute_frequency_available` had to be redefined). Parser ([parser.py L14–23](file:///e:/Hackathon/SIH2026/main_version1/backend/ingestion/parser.py#L14-L23)) **ignores all `autosig:*` fields** — only `core:sample_rate`, `core:datatype`, `core:frequency` are consumed |
| `models/modulation_cnn.metrics.json` | `held_out_window_accuracy: 0.9744` over 156 windows | Derived from manifest labels |
| Source-code constants | `PREAMBLE`, `HEADER`, `GENERATORS`, `CONSTRAINT_LENGTH`, rows=12, seed 20260922, noise seeds 42/43, `SAMPLE_RATE`, `SAMPLES_PER_SYMBOL`, `±85 Hz`, SNR set | Authoritative, in git |
| No `.yaml/.yml/.npz/.csv/.pkl/.h5/parquet/logs` anywhere | (globbed — zero results) | — |

## 7. System claim vs available ground truth

| System claim | GT currently available? | Valid to measure quantitatively? | Why/why not |
|---|---|---|---|
| Modulation classification | Yes (`label`) | **Yes** | Per-file label, RNG-reproducible; caveats in §10 about train/test correlation |
| CFO estimation | Yes (`frequency_offset_hz`, verified injected) | **Yes** | This is the Step-2 basis; legitimate |
| SNR estimation | Yes (`snr_db`) | **Yes, with definition caveat** | Manifest SNR is symbol-power/complex-noise-power per fallback L26; an estimator using a different in-band/noise-floor definition can legitimately differ |
| Occupied bandwidth | Only indirectly | **Partially** | True bandwidth is a deterministic function of the rectangular pulse at 6000 baud (null-to-null 12 kHz); derivable but never recorded; no shaped-pulse cases exist |
| Symbol-rate estimation | Trivially (6000 always) | **No — degenerate** | A single constant GT cannot score an estimator |
| Synchronization (timing) | GT is 0 for every file | **No — degenerate** | Nothing was offset; a timing search trivially "wins" at its own convention |
| Phase recovery | GT phase is 0 for every file | **No** | No random initial phase was ever injected; the ambiguity search is tested only against the map's natural states |
| Demodulation (bit accuracy vs truth) | Yes via seeded reproduction (396 transmitted bits/file) | **Yes — but not currently done** | No code today compares recovered bits to the reproduced `ilv`; only preamble correlation is used |
| FEC decoding | Scheme identity only | **Partially** | The *transmitted* encoded sequence is reproducible, so post-FEC frame-bit accuracy is measurable; but with no channel diversity (one noise seed) it is not a coding-gain evaluation |
| Deinterleaving | Scheme identity + reproducible sequence | **Partially**, same caveat | Only one interleaver exists; nothing to disambiguate |
| Bitstream recovery (payload) | Yes via reproduction | **Yes — but currently unclaimed/unmeasured** | The payload is never compared to GT anywhere in the app; "recovered bitstream" is displayed, not scored |
| Frame validation | Yes (`PREAMBLE` constant) | **Yes, as designed** | It validates preamble presence ≥ 0.90, which is what it claims — see §8 |

## 8. The validation mechanism, precisely

- **Exact preamble:** `PREAMBLE = 11010011100100011101001110010001` — [coding.py L7](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/coding.py#L7). ⚠ Forensic note: it is the 16-bit word `1101001110010001` **repeated twice** (autocorrelation 0.5 at lag 16). Threshold 0.90 > 0.5, so no false-pass from the self-repeat, but it's a weak pattern for sidelobe analysis.
- **Where generated:** embedded by `make_frame()` (coding.py L74–75), called both by the dataset generator (L61) and by the recovery chain's re-encoder — same constant, single source of truth.
- **What the validator does:** [validate_bitstream](file:///e:/Hackathon/SIH2026/main_version1/backend/validation/correlation.py#L9-L21) ±1-correlates the *recovered* bitstream against that constant, `score = peak/32`, `passed = score ≥ 0.90`; header split at `peak_index+64`.
- **Is it validating correctness?** It is **detecting a known synthetic pattern within the recovered stream**. Because that pattern can only appear if sync→demod→deinterleave→Viterbi all ran coherently, it is strong *evidence of a working chain* — but it is not a payload-correctness check, and it is not compared against per-file ground truth bits.
- **Would it work on an unknown real capture?** **No.** It requires the preamble to be known a priori (it's a compile-time constant). The [docs/06 L9](file:///e:/Hackathon/SIH2026/main_version1/docs/06-validation-correlation.md) claim that "the same principle applies" off-air is aspirational, not implemented. This is **synthetic-corpus validation, full stop**: correlation against a pattern we planted.

## 9. Re-check of the Step 2 CFO audit — verdict: **legitimate ground truth**

`manifest.frequency_offset_hz` is genuinely the injected CFO, established three independent ways:
1. **Code path:** the same `offset_hz` float flows from L66 → `run_flowgraph(..., offset_hz, ...)` L69 → rotator phase ramp (fallback L24) → written at L74. No re-estimation, no filename parsing, anywhere in that chain.
2. **Replay:** seeded RNG reproduction matches all 64 manifest values bit-exactly (0 mismatches).
3. **Waveform:** regenerated captures are **byte-identical** to the corpus files (max diff 0.0), which is only possible if the impairment used exactly that frequency.

The Step 2 A/B compared estimators against the true injected value at full float precision (not the rounded filename values). **No redo needed; the baseline stands.**

## 10. Dangerous / overstated claims found

| Where | Claim | Problem |
|---|---|---|
| All 64 `.sigmf-meta` files | `"core:description": "GNU Radio generated …"` | **False** — `generator` field says fallback for 64/64. Contradicts README L31 "it never pretends fallback captures are GNU Radio captures" |
| [docs/07-data-generation.md](file:///e:/Hackathon/SIH2026/main_version1/docs/07-data-generation.md), docs/03 L26 | dataset "generated by GNU Radio" | Active generator is the NumPy fallback; GNU Radio path is untested code |
| [README.md L13](file:///e:/Hackathon/SIH2026/main_version1/README.md) | "both are fully demodulated and validated" | "Validated" = preamble correlation ≥ 0.90, not payload-vs-truth; and corpus-wide frame-validation pass rate is 42/64 IQ |
| docs/model-training.md L27 | ground truth "is the only way to *prove* the pipeline is correct" | Proves correctness only over a channel family of {AWGN, CFO∈±85 Hz, zero timing, zero phase offset, rectangular pulses, one reused noise realization} — external validity to real captures is unestablished |
| `models/modulation_cnn.metrics.json` "held_out_window_accuracy 97.4%" | Label GT is legitimate, but **files share the same noise realization** and window splits are random over near-duplicate ensembles → the number is plausibly optimistic |
| docs/06 L9 | off-air "the same principle applies using whatever preamble… is expected" | No such configurable validator exists; `PREAMBLE` is a module constant |
| UI "✓ Validated Recovery", Report "validated" wording | Implies bit-level correctness assurance | Only preamble detection is asserted; acceptable if wording stays "frame validation" and never "correctly recovered bits" — current Step-1/2 fixes kept it there; keep it |
| [tools/cfo_ab_report.py L4](file:///e:/Hackathon/SIH2026/main_version1/tools/cfo_ab_report.py) "true CFO from the manifest (ground truth)" | Now **justified** by §9 — no action needed | — |

No dangerous claims found in tests: `tests/` generates its own signals by construction (self-consistent GT, honestly scoped).

## 11. Final classification

### A. Ground truth we definitely have (recorded, verified injected)
Per-file **modulation label, SNR dB, frequency offset Hz (full precision), sample rate** — in `manifest.json` and duplicated in sigmf-meta annotations; **proven** to be the actual impairment values by bit-identical regeneration. Also the **fixed channel model itself**: AWGN + single rotator, rectangular pulses, no timing/phase/multipath offsets, Block-12 + rate-½ K=7 Viterbi, 8 sps, 6000 baud.

### B. Probably-have but not centrally recorded — *and now upgraded to verified*
**Payload bits, full frame, encoded/interleaved sequence, exact noise realization** — not in any manifest, but reproducible bit-identically from `generate(seed=20260922)` + code constants (`PREAMBLE`, `HEADER`, `GENERATORS`). This is only as durable as the generator code and seed remaining unchanged in git; it is reproduction, not recorded metadata.

### C. Parameters we cannot legitimately evaluate
- **Timing-offset estimation/recovery** (GT always 0)
- **Initial carrier phase estimation** (GT always 0; never randomized)
- **Symbol-rate estimation** (single constant 6000 baud)
- **Occupied-bandwidth estimation against realistic shaping** (no pulse filter ever applied)
- **FEC coding gain / BER curves** (one shared noise realization, one channel family)
- **Anything on real-world captures**: off-air the preamble, `PREAMBLE`-known frames, and labels are unavailable by definition

### D. Claims that should NOT be made
(1) "GNU Radio–generated dataset" (metadata, README, docs/03, docs/07); (2) "fully demodulated and validated" / any claim that recovered bits are *verified correct* — only preamble presence is verified; (3) presenting 97.4% held-out accuracy without the shared-noise/near-duplicate-window caveat; (4) implying frame validation generalizes to unknown off-air signals; (5) any sync/phase/timing "accuracy" claim that treats the constant-zero GTs as measured variation.

### E. Recommended Step 3 direction — **recommendation only, not implemented**
Priority order based on the gaps above:
1. **Close the payload-truth loop:** add a corpus-wide evaluation that compares the chain's recovered payload bits against the reproducible transmitted frame (Class B), turning "preamble detected" into measured bit/frame error rate per SNR — cheap, uses existing reproduction, no regeneration needed.
2. **Diversify the corpus (regeneration, later):** randomize initial carrier phase, timing offset, pulse shaping, per-file noise seeds, and payload lengths — currently entire evaluation dimensions are degenerate (§11C). This is a dataset change, so gate it behind your explicit go.
3. **Fix the label honesty in metadata** (`core:description`, README/docs GNU Radio wording) — small, non-breaking.
4. **Record Class-B truth in the manifest** (payload/frame bit digest or index) so ground truth stops depending on byte-exact code reproduction.

I have changed nothing. Tell me which of E1–E4 (if any) Step 3 should take on, and I'll plan it before touching code.