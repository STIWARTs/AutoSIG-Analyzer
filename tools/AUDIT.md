I'll audit the actual implementation systematically. Let me start by mapping the codebase structure and reading the core pipeline.


The files are surprisingly compact. Let me read the entire backend core.


Now the recovery chain, ML, hypotheses, ingestion, and validation.


Now the UI layer to see how parameters are displayed.


Now the analysis page (display logic), remaining backend modules, and training.


Now storage, correlation module, training, and dataset metadata to verify assumptions.


Let me check the remaining small modules and documentation that states intent.


I have the full code picture. Now let me empirically verify the numerical behavior by running the actual pipeline functions (read-only, no files written, no DB save).


Reproduced the exact observed case. Now let me trace the recovery internals for that file and test my structural hypotheses.


Two smoking guns found. Let me quantify them with a controlled experiment across the corpus.


One final empirical check on the displayed-parameter accuracy (SNR, bandwidth, CFO refusal rate).


## Audit scope note

I read every source file in `backend/`, `app/`, `training/`, `gnuradio/`, `tests/`, plus `docs/` and `README.md`, and then ran the actual functions against `datasets/*.iq` **in-memory via stdin** to measure real behavior. **No file was created, modified, or deleted** (I deliberately avoided `save_analysis()` so `data/autosig.db` was untouched). Every claim below is either a line reference or a measurement I reproduced.

I also identified the exact capture behind your observed result: **`datasets/bpsk_030_snr-2_cfo+62.iq`** — it reproduces your panel digit-for-digit (48000 / 47625 / 62.3391 / 62.3391 / 8.4987 / 833.33, BPSK 89.1%, corr 0.500 and 0.438).

---

# 1. Complete execution flow (actual)

| Stage | File · function | What it really does |
|---|---|---|
| Upload / pairing | [streamlit_app.py:36-45](file:///e:/Hackathon/SIH2026/main_version1/app/streamlit_app.py#L36-L45) | `type=None` uploader; pairs `.iq` with `.sigmf-meta` by filename stem; `.wav` treated as single-file |
| Manual metadata | [streamlit_app.py:57-72](file:///e:/Hackathon/SIH2026/main_version1/app/streamlit_app.py#L57-L72) | Only shown for `.iq` **without** sidecar. WAV can never get a center frequency |
| Ingestion | [parser.py:83-90](file:///e:/Hackathon/SIH2026/main_version1/backend/ingestion/parser.py#L83-L90) `parse_upload` → `load_iq` / `load_wav` | → `IngestedSignal(samples, sample_rate, center_frequency, source_format, metadata)` |
| SigMF fields | [parser.py:14-23](file:///e:/Hackathon/SIH2026/main_version1/backend/ingestion/parser.py#L14-L23) `_sigmf_fields` | `sample_rate` **required** (raises otherwise); center from `captures[0]["core:frequency"]` falling back to `global` |
| IQ decode | [parser.py:26-34](file:///e:/Hackathon/SIH2026/main_version1/backend/ingestion/parser.py#L26-L34) `_decode_iq` | `cf32_le` / `ci16_le` only, little-endian hardcoded |
| Preprocessing | [analysis.py:81-85](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L81-L85) `prepare_samples` | **DC removal only.** No filtering, no resampling, no normalization |
| ML inference | [classifier.py:52-59](file:///e:/Hackathon/SIH2026/main_version1/backend/ml/classifier.py#L52-L59) `classify_samples` | ≤32 windows × 256 samples, per-window power norm, CNN, softmax, **mean over windows** |
| DSP analysis | [analysis.py:88-126](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L88-L126) `analyze_signal` | Welch PSD, STFT, 6 parameters. Receives `modulation=` from ML |
| Hypotheses | [engine.py:6-11](file:///e:/Hackathon/SIH2026/main_version1/backend/hypotheses/engine.py#L6-L11) `build_hypotheses` | Top-K of the probability dict; interleaving/FEC are **string constants** |
| Recovery | [chain.py:22-64](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/chain.py#L22-L64) `run_recovery` | sync → demod → de-interleave → Viterbi (**per hypothesis**) |
| Validation | [correlation.py:9-21](file:///e:/Hackathon/SIH2026/main_version1/backend/validation/correlation.py#L9-L21) `validate_bitstream` | ±1 correlate vs 32-bit `PREAMBLE`, `score = peak/32`, `passed = score ≥ 0.90` |
| Accept/reject | [pipeline.py:20-38](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L20-L38) | first `passed` becomes `accepted`; **all** hypotheses still run |
| Persist / render | [streamlit_app.py:81](file:///e:/Hackathon/SIH2026/main_version1/app/streamlit_app.py#L81) → [history.py:203-238](file:///e:/Hackathon/SIH2026/main_version1/backend/storage/history.py#L203-L238) | full `PipelineResult` serialized to `result_json` |

There is **no separate "demodulation stage", "bitstream validation stage" or "frame validator"** in code beyond the above; `backend/correlation/` is a one-line docstring stub ([correlation/\_\_init\_\_.py](file:///e:/Hackathon/SIH2026/main_version1/backend/correlation/__init__.py)).

---

# 2. DSP vs ML ordering — the real dependency graph

**ML runs FIRST. DSP runs second. The docs' diagram (DSP → ML) is inverted relative to the code.** This is deliberate; the comment at [pipeline.py:12-13](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L12-L13) states the reason.

```text
.iq / .wav + SigMF
  ↓ parse_upload → IngestedSignal
  ↓ prepare_samples()                 [DC removal — pure DSP, ML-free]
  ↓ classify_samples()                ← ML (CNN)  ── probabilities {BPSK, QPSK}
  ↓                                        ↓ argmax(probabilities)
  ↓ analyze_signal(modulation=<ML top class>)     ← DSP block, PARAMETERISED BY ML
  ↓ _estimate_carrier_offset(x, fs, modulation)   ← the ONLY ML-dependent DSP calc
  ↓ build_hypotheses(probabilities)
  ↓ run_recovery(samples, hypothesis)   per hypothesis
       ↓ synchronize_psk(...)           ← 3rd, independent CFO estimator
       ↓ demod / deinterleave / viterbi
  ↓ validate_bitstream(...) → Frame Validation PASS/FAIL
```

Precise answers:

- **Does DSP run before ML?** Partly: `prepare_samples` (DC removal) is the only DSP that precedes ML, and ML consumes its output.
- **Does ML run before DSP?** Yes, for everything labelled "measured parameters".
- **Independent/parallel?** No. Strictly sequential, single-threaded, one process.
- **Does any DSP function depend on the ML prediction?** Yes — exactly one: [`_estimate_carrier_offset`](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L39-L78) via the `modulation` argument (selects `orders = (2,)`, `(4,)`, or `(2,4)`). `analyze_signal` itself takes `modulation` only to forward it.
- **Does ML depend on any DSP-derived feature?** Only on DC removal. It uses **raw I/Q**, not PSD/SNR/CFO/bandwidth/symbol rate. No feature vector exists.
- **ML-independent DSP:** Welch PSD, STFT waterfall, `_occupied_bandwidth`, `_estimate_snr`, `_estimate_symbol_rate`, all of `synchronize_psk`, all of the recovery chain.
- **ML-dependent DSP:** only the power-law **order selection** inside `_estimate_carrier_offset`.

Two consequences worth knowing:
1. The `(2, 4)` "no hint" branch at [analysis.py:54-55](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L54-L55) is **effectively dead code** — `modulation` is always `"BPSK"` or `"QPSK"` because those are the only classes in the checkpoint.
2. Because ML picks the estimator order **before** the measurement, a misclassification can silently switch the CFO estimator to a wrong power law. There is no confidence check on the argmax (89.1% and 51% are treated identically).

---

# 3. CFO / carrier offset — every implementation

There are **two independent estimators plus a third phase-only mechanism.** None is connected to any other.

### Estimator #1 — DSP spectral power-law (`backend/dsp/analysis.py:39-78`)
1. **Where first estimated:** inside `analyze_signal`, after PSD/STFT, line 114.
2. **Algorithm:** raise the complex signal to the `order`-th power → subtract mean → **8× zero-padded** FFT (`n = 8*len(x)`) → search `|f| < fs/8` for the max bin → **parabolic (3-point quadratic) interpolation** of the peak → divide the peak frequency by `order`. Quality gate: `peak / mean(band) ≥ 4.0`, else return `None`. If `modulation` is unknown/other, both orders 2 and 4 are tried and the **higher concentration score** wins.
3. **Inputs:** DC-removed complex samples, `fs` (returns `None` if `fs is None`), ML class.
4. **Needs classification?** Yes, softly — only to choose the power law.
5. **How modulation affects it:** BPSK → `x²` (noise-optimal, `x²` is a pure tone); QPSK → `x⁴` (strips the modulation). Wrong choice still works but is noisier (`x⁴` on BPSK is legal, `x²` on QPSK is not — QPSK `x²` has no tone).
6. **Stored?** Yes: `parameters["carrier_offset_hz"]`, and it is the *only* CFO value that reaches the UI, the JSON report, and SQLite.
7. **Passed into recovery?** **NO.** `run_recovery(analysis.signal.samples, hypothesis)` at [pipeline.py:24](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L24) passes **samples and hypothesis only**. I grepped: `carrier_offset_hz` is referenced by exactly two consumers — the Analysis page display and `_nullable_float(params.get(...))` for the DB column. Nothing in `backend/recovery/` or `backend/dsp/sync.py` reads it.
8. **Does recovery re-estimate?** Yes, from scratch, every hypothesis.
9. **Hint / initial value / correction / unused?** **Completely unused.** No initialisation, no comparison, no sanity check against it.
10. Grep-confirmed: no other file mentions Costas, phase-locked loop, frequency discriminator, or Gardner.

### Estimator #2 — sync unwrapped-phase slope (`backend/dsp/sync.py:6-26`)
```python
powered = x ** order                    # order = 4 if QPSK else 2, from the HYPOTHESIS
phase   = np.unwrap(np.angle(powered))
slope   = np.polyfit(np.arange(len(phase)), phase, 1)[0]   # ordinary least squares
cfo_rad_per_sample = slope / order
corrected = x * np.exp(-1j * cfo_rad_per_sample * np.arange(len(x)))
```
- Rad/sample, not Hz. Whole-record open-loop fit. **No zero padding, no DC-term removal, no interpolation, no amplitude information, and no quality gate whatsoever.** `polyfit`'s intercept (the constant phase `order·φ₀`) is **discarded** — only `[0]` is taken.
- Modulation enters through `order` (per hypothesis, so H1 and H2 estimate different CFOs on the same signal).
- Reported as `Synchronization · PASS · CFO 0.01611 rad/sample`.

### Mechanism #3 — residual phase-state search (`backend/recovery/chain.py:36-52`)
Not a frequency estimator: it tries `phase_index * π/2` (4 states for QPSK, **2 for BPSK**) and keeps the argmax of the preamble correlation.

### Measurements on the real corpus (fs = 48 kHz, true CFO from filename)

| true SNR | DSP estimator median abs error | sync estimator median abs error | sync max | DSP refused |
|---:|---:|---:|---:|---:|
| −2 dB | **0.28 Hz** | **106.5 Hz** | 216.5 Hz | 6/12 |
| 0 dB | 0.19 Hz | 83.4 Hz | 132.7 Hz | 6/12 |
| +4 dB | 0.48 Hz | 38.2 Hz | 124.5 Hz | 0/10 |
| +8 dB | 0.24 Hz | 24.9 Hz | 129.6 Hz | 0/10 |
| +12 dB | 0.24 Hz | 2.9 Hz | 26.7 Hz | 0/10 |
| +18 dB | 0.30 Hz | 0.21 Hz | 0.6 Hz | 0/10 |

The **displayed** CFO is accurate to well under 1 Hz everywhere it reports at all. The **recovery** CFO is off by ~100 Hz exactly where recovery is already struggling. For your observed file: DSP = 62.339 Hz (truth = 62 Hz); sync = 0.016112 rad/sample = **123.09 Hz** — essentially **2× the true offset**, leaving ~61 Hz residual, i.e. ≈25 full constellation rotations across the 3168-sample record.

The reliability ordering is inverted: the estimator that is **gated and refuses** is the accurate one; the estimator that **always reports PASS** is the unreliable one.

---

# 4. What "center frequency" currently means

[analysis.py:114-125](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L114-L125):
```python
carrier_offset   = _estimate_carrier_offset(x, processed.sample_rate, modulation)
absolute_available = has_rate and processed.center_frequency is not None
center = (processed.center_frequency or 0.0) + carrier_offset if carrier_offset is not None else None
```

**Yes — the application literally does `center = metadata_center + estimated_offset`.** Precisely:

- **Where the anchor comes from:** `captures[0]["core:frequency"]`, else `global["core:frequency"]` ([parser.py:20](file:///e:/Hackathon/SIH2026/main_version1/backend/ingestion/parser.py#L20)), else the manual text field ([streamlit_app.py:62](file:///e:/Hackathon/SIH2026/main_version1/app/streamlit_app.py#L62)).
- **When it is `0`:** `(0.0 or 0.0) + offset = offset`. Since every generated sidecar writes `"core:frequency": 0.0` ([generate_dataset.py:40](file:///e:/Hackathon/SIH2026/main_version1/training/generate_dataset.py#L40)), `center_frequency_hz` is **numerically identical** to `carrier_offset_hz` — exactly the duplicated 62.34 / 62.34 you saw.
- **When it is missing:** `None or 0.0 → 0.0`, so the arithmetic is unchanged and **nothing distinguishes "anchor is 0 Hz" from "anchor is unknown"**. This is the WAV path (`center_frequency=None`, [parser.py:79](file:///e:/Hackathon/SIH2026/main_version1/backend/ingestion/parser.py#L79)), which also has no manual-override UI.
- **Absolute or relative?** Almost always **relative baseband**. For 100% of `datasets/` (all `core:frequency: 0.0`) and for every WAV upload, `center_frequency_hz` is a baseband offset of a few tens of Hz. It becomes a genuine RF frequency only if a nonzero RF anchor is supplied.
- **Can the UI mislabel it? Yes, currently it does.** Two concrete defects:
  1. `absolute_frequency_available` is computed [line 115](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L115) and then **explicitly skipped** by the only renderer: [`if key == "absolute_frequency_available": continue`](file:///e:/Hackathon/SIH2026/main_version1/app/pages/analysis.py#L34-L35). It is never surfaced anywhere (not even a DB column). So the table prints a row labelled **"center frequency Hz" = 62.34** with no relative/absolute qualifier.
  2. Even if it *were* surfaced, its definition is wrong: it is `True` whenever a frequency key merely *exists* — so a `0.0` placeholder (the entire shipped corpus) reports "absolute frequency available". For your observed file the flag was **1.0** while the value was pure baseband.
- A missing sample rate is handled correctly: `_estimate_carrier_offset` returns `None` → `center` is `None` → the row shows `UNAVAILABLE` plus a warning banner.

---

# 5. Symbol-rate estimation

[`_estimate_symbol_rate`](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/analysis.py#L24-L36):
```python
y = x[: min(len(x), 32768)] ** 4                       # always order 4, fixed
spectrum  = np.abs(np.fft.fft(y * np.hanning(len(y))))
frequencies = np.fft.fftfreq(len(y), 1/fs)
candidates = (frequencies > fs/200) & (frequencies < fs/2.2)   # positive freqs only
return frequencies[candidates][argmax(spectrum[candidates])]
```

- **Algorithm:** single plain (non-zero-padded, non-interpolated) Hann-windowed periodogram of the **fourth-power** signal, restricted to 240 Hz – 21.8 kHz; highest bin wins. No DC removal, no averaging, no peak-significance test — **no refusal gate at all**.
- **Input:** DC-removed samples, first 32768, always `x⁴`.
- **Modulation classification used?** **No.** Deliberately fixed at 4 (comment says "Fourth-power removes QPSK data modulation").
- **Sample rate required?** Yes — returns `None` when `fs is None`.
- **Metadata?** No; there is no symbol rate anywhere in `IngestedSignal` or the schema. Pure estimate.
- **Where consumed?** Display row `estimated symbol rate baud`, SQLite column, report JSON. **Nothing in recovery.** `run_recovery`'s `samples_per_symbol: int = 8` ([chain.py:22](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/chain.py#L22)) is **never overridden** — grep confirms no caller passes it. So the one quantity that would let the DSP feed timing is measured and then discarded.

**Limitations, proven by measurement, not theory.** True symbol rate for every capture is 6000 baud (48000/8). The 52 non-`None` estimates spread from **242 Hz to 20818 Hz** with no clustering near 6000. And the low values are not noise — they are **4× the carrier offset**, because for ideal PSK `x⁴` is a pure tone at `4·Δf`, not a symbol-rate line (rectangular `repeat` pulses produce no symbol-rate discrete line, [synthetic_flowgraph.py:37](file:///e:/Hackathon/SIH2026/main_version1/gnuradio/synthetic_flowgraph.py#L37)):

| file | true CFO | 4·CFO | reported "symbol rate" |
|---|---:|---:|---:|
| bpsk_003 | 75 | 300 | **303.0** |
| bpsk_009 | 81 | 324 | **318.2** |
| bpsk_011 | 79 | 316 | **318.2** |
| bpsk_016 | 70 | 280 | **272.7** |
| bpsk_031 | 68 | 272 | **272.7** |
| qpsk_008 | 60 | 240 | **242.4** |
| qpsk_023 | 75 | 300 | **303.0** |

So this estimator is, in a large fraction of cases, **a badly-scaled duplicate of the CFO measurement** (it even forgot to divide by 4), and otherwise a noise peak. Your 833.33 is a noise peak.

---

# 6. The recovery chain, stage by stage

```
Synchronization → Demodulation → De-interleaving → FEC → (Frame Validation, in pipeline)
```

### Synchronization — [sync.py:6-26](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/sync.py#L6-L26)
- **Receives:** DC-removed samples; `samples_per_symbol = 8` (**hardcoded assumption**); `hypothesis.modulation`. Does **not** receive DSP CFO or symbol rate.
- **Produces:** decimated symbol array + `{cfo_rad_per_sample, timing_offset, timing_metric}`.
- **Assumptions:** exactly 8 samples/symbol; integer timing only (`for offset in range(samples_per_symbol)` — **no fractional-offset interpolator, no Gardner/M&M loop**); no pulse shaping; CFO constant over the record; phase unwrapping succeeds.
- **Can it output garbage and continue?** Yes. It has exactly one failure mode — `len(x) < sps*16` (128 samples) raises.
- **PASS means:** *"the function returned."* Nothing more. `timing_metric` (a real lock-quality number) is computed at [line 20-22](file:///e:/Hackathon/SIH2026/main_version1/backend/dsp/sync.py#L20-L22) and then **never used as a gate** — it isn't even displayed. Your run: metric **0.0863** for BPSK (essentially no constellation concentration) → badge **PASS**.

### Demodulation — [chain.py:11-19, 36-58](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/chain.py#L36-L58)
- Hard decisions only: `real < 0` for BPSK, Gray quadrant pair for QPSK. **No soft metrics** → Viterbi gets 1-bit/hard decisions, losing ~2 dB.
- Before deciding, it **trials every phase state, decodes the whole chain for each, and keeps the one with the highest preamble correlation** ([chain.py:38-48](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/chain.py#L38-L48), using `validate_bitstream(..., threshold=-1)`). This is legitimate ambiguity resolution for QPSK's 4 states, but note two things: (a) the known preamble is **used inside recovery to select a physical parameter**, and (b) for **BPSK the grid is `{0°, 90°}`** — it tries the nonphysical 90° state and **never tries the true 180° flip** that the code comment at [lines 30-34](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/chain.py#L30-L34) says it is resolving. `phase state 1` in your output = a 90° rotation, i.e. BPSK decisions taken on the (near-empty) imaginary axis.
- **PASS means:** *"the loop completed."* Always true.

### De-interleaving — [coding.py:67-71](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/coding.py#L67-L71)
- `reshape(-1, 12).T.reshape(-1)`. Fixed 12 rows; `hypothesis.interleaving` is **never read**. PASS = the `% 12` truncation upstream guarantees the modulo check can't fire, so **PASS is structurally guaranteed**. Pure permutation: always produces same-length output regardless of correctness.

### FEC — [coding.py:27-57](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/coding.py#L27-L57)
- Rate-1/2, K=7, generators (0171, 0133), terminated, hard 2-bit Hamming branch metric, pure-Python double loop. `hypothesis.fec` **never read** — every hypothesis is decoded with the same code.
- **It always emits `len/2 - 6` bits.** Viterbi is ML sequence estimation: with a wrong input it returns the *closest wrong path*, indistinguishable in structure from a right answer. PASS = *"the traceback finished."* No path-metric, no residual-metric, no convergence check is exposed — `metrics` is discarded at [line 50](file:///e:/Hackathon/SIH2026/main_version1/backend/recovery/coding.py#L50).
- Runs ~4× (once per phase state) × 2 hypotheses in pure Python; this is the dominant cost of a run.

### Frame Validation — [pipeline.py:28-30](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L28-L30)
- The **only** stage whose status encodes a correctness claim: `correlation_peak / 32 ≥ 0.90`.
- **It can fail after everything PASSes because those PASSes make no correctness claim.** This is by design of the status vocabulary, not a bug in a given stage.

### One display/semantics bug in this area
[bitstream.py:35](file:///e:/Hackathon/SIH2026/main_version1/app/pages/bitstream.py#L35): `("Phase state", f"{accepted.hypothesis.rank}")` — renders the **hypothesis rank** as the carrier phase state. And [pipeline.py:36](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L36): when nothing passes, `result.validation = validations[max(validations)]` selects the **highest-ranked-number** attempt (i.e. the *last* tried, typically the *weakest*), not the best score — so your stored/reported correlation is **0.438 (H2)**, not the maximum observed.

---

# 7. Hypothesis generation — exactly how Top-K is built

[engine.py:6-11](file:///e:/Hackathon/SIH2026/main_version1/backend/hypotheses/engine.py#L6-L11), all 6 lines:
```python
ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[:top_k]
return [Hypothesis(rank=i+1, modulation=m, interleaving="Block",
                   fec="Convolutional / Viterbi", score=s) for i,(m,s) in enumerate(ranked)]
```

- **From ML:** the modulation label and `score` — nothing else.
- **Predefined constants:** `interleaving="Block"`, `fec="Convolutional / Viterbi"` — literal strings, identical in every hypothesis, and (as §6 shows) **never consulted by `run_recovery`**, which unconditionally runs the 12-row block inverse and the 0171/133 Viterbi.
- **Probability use:** raw softmax mean-over-windows, used only as a **sort key**. Never thresholded, never combined with DSP evidence, never propagated as uncertainty. `top_k=2` from [pipeline.py:11](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L11); with `CLASS_NAMES = ("BPSK","QPSK")`, `top_k=2` ⇒ **the hypothesis list is always both classes in probability order** — it is a permutation, not a selection.
- **Ranking:** descending probability. So `Hypothesis 1 · 89.1%` is literally `P(BPSK)`, and the Recovery screen's caption "each candidate is recovered and validated in order" is accurate.
- **Are FEC/interleaving predicted or tested?** As written, **neither**. There is no FEC/interleaving search space at all — they are asserted. Because the *labels* never change behaviour, no hypothesis with a different FEC would decode differently; the "hypothesis" axis that actually exists is **modulation only**.

---

# 8. Analysis of your observed result

Everything below was reproduced from `datasets/bpsk_030_snr-2_cfo+62.iq` (true: BPSK, **SNR −2 dB**, **CFO +62 Hz**, sps 8 → **6000 baud**, 3168 samples = 396 symbols, 198 payload bits → 400 coded… frame of 192 decoded data bits).

### What each PASS means
| Badge | Actual meaning in code |
|---|---|
| `Synchronization PASS` | `synchronize_psk` did not raise (only possible raise: <128 samples). The CFO value printed is the estimate, **whatever it is**. Your run: 0.01611 rad/sample = **123.09 Hz vs a true 62 Hz** |
| `BPSK/QPSK Demodulation PASS` | the phase-state loop finished and a winner was chosen |
| `Block De-interleaving PASS` | a reshape succeeded — **guaranteed** by the `% 12` truncation just above it |
| `Viterbi FEC PASS` | the trellis traceback returned an array |
| `Frame Validation FAIL` | best-of-phase-trials preamble correlation `< 0.90` — **the only meaningful verdict in the list** |

So: **4 free structural PASSes, then 1 real test.** The panel reads "everything worked except the last check", while the truth is "nothing before the last check asserted anything."

### Why validation still fails after all that
Because the four preceding badges are execution receipts, and the bit error rate arriving at the correlator is far above what a rate-1/2 K=7 code with **hard** decisions can fix.

### Where a wrong CFO/sync estimate bites
Residual CFO → the constellation rotates continuously. Here the sync estimate was ~2× too large, leaving ≈61 Hz → `360° × 61 × 3168 / 48000 ≈ 25` full rotations over the record → hard decisions flip in bursts → Viterbi emits a plausible-looking but wrong sequence → correlation lands near chance. The residual constant phase (the discarded `polyfit` intercept) and the `{0°,90°}` BPSK grid compound it. `timing_metric = 0.086` shows the symbol clock/constellation was never locked — and was ignored.

### Are the reported CFO and the synchronization CFO the same quantity?
Same *physical* quantity (carrier rotation rate), but:

| | Analysis panel "carrier offset" | Sync "CFO" on the recovery step |
|---|---|---|
| Function | `_estimate_carrier_offset` | `synchronize_psk` |
| Algorithm | 8× zero-padded periodogram of `x²`/`x⁴` + parabolic interpolation, mean-subtracted, band-limited to `fs/8` | OLS slope of `unwrap(angle(x^order))`, no padding/interpolation/mean removal |
| **Unit** | **Hz** | **rad/sample** |
| Order source | **ML argmax** | **hypothesis being tested** |
| Data used | full record | full record |
| Quality gate | peak ≥ 4× band mean, else refuse | **none** |
| Result (your file) | 62.34 Hz (err 0.34 Hz) | 0.016112 rad/sample = 123.09 Hz (err 61.1 Hz) |
| Used by recovery | **no** | yes |

**Same physical quantity, different estimators, different units, different modulation source, no shared code, no cross-check, and no conversion anywhere in the repository** — I grepped for `2 * np.pi` / `fs /` conversions involving either: the only place Hz and rad/sample coexist is in my own diagnostic. To convert: `rad/sample × fs / 2π = Hz` (`0.008056 × 48000 / 2π = 62.0 Hz`). Also, both hypotheses report *different* CFOs for the same signal (0.01611 BPSK vs 0.00277 QPSK) — a self-inconsistency the UI never surfaces.

### Are 0.500 / 0.438 meaningful near-misses?
No — they are quantised chance. `len(PREAMBLE) = 32`, and with ±1 mapping every correlation value is an even integer, so **scores can only be multiples of 1/16 = 0.0625**: 0.500 = 16/32, 0.4375 → "0.438" = 14/32. A maximum over 2–4 phase trials drawn from a bitstream with ~25% BER is a selection-inflated coin flip. Displaying "Correlation 0.500" next to a 0.90 threshold invites reading it as "halfway to success"; it is in fact indistinguishable from no lock (16 of 32 preamble bits right by chance).

### The panel's own numbers misdescribe this capture
| Displayed | True | Nature of the gap |
|---|---|---|
| SNR 8.50 dB | **−2 dB** | `_estimate_snr` is `P90(dB PSD) − P20(dB PSD)`, not SNR. Measured bias over the corpus: **+11.6 dB at −2 dB, +10.5 at 0, +8.2 at +4, +7.1 at +8, +5.3 at +12, +2.3 at +18**. It is a spectral-spread statistic, and it is **computed even when `fs` is unknown** (unlike every other parameter) |
| Bandwidth 47625 Hz | ~12000 Hz main lobe | `_occupied_bandwidth` masks at `P20 + 6 dB`; these captures' main lobe never clears 6 dB over that floor, so the mask picks noise bins across the whole band → returns ≈ `fs − 375`. Corpus medians: **46.1–47.5 kHz regardless of signal** |
| Symbol rate 833.33 baud | 6000 baud | see §5 — usually 4×CFO or a noise bin |
| Center freq 62.34 Hz | not an RF frequency | relative baseband; see §4 |

The important corollary: **these three inflated/incorrect readings are what make the failure look contradictory.** The panel advertises an "8.5 dB SNR, 6000-ish-baud-looking signal with a clean 62 Hz CFO", so recovery *should* work; the actual capture is −2 dB SNR, where recovery is information-theoretically out of reach for this chain.

### Is the CFO the binding constraint? (oracle test)
I re-ran the identical chain with a **perfectly known CFO from the filename**:

| true SNR | n | current sync CFO | DSP spectral CFO | **oracle CFO** |
|---:|---:|---:|---:|---:|
| −2 dB | 12 | 1 | 1 | **1** |
| 0 dB | 12 | 0 | 0 | **0** |
| +4 dB | 10 | 0 | 1 | **1** |
| +8 dB | 10 | 3 | 3 | **3** |
| +12 dB | 10 | 6 | 6 | **6** |
| +18 dB | 10 | 10 | 10 | **10** |
| **total** | **64** | **19** | **21/52** | **21/64** |

Stated honestly because it constrains the diagnosis: **wiring the DSP CFO into recovery would change almost nothing on this corpus.** Even with the exact true offset, low-SNR captures still fail — the limiter at ≤ +4 dB is hard-decision demodulation of a 396-symbol record at −2 dB, not the CFO. Conversely, the CFO disconnect is still a genuine architectural defect (an accurate, gated estimate is discarded in favour of an ungated one that errs by ~100 Hz), but its observable cost today is **credibility of the displayed numbers**, not pass rate. Where a wrong CFO *would* dominate is a capture with real timing drift or large offsets — which the shipped corpus does not contain (`epsilon=1.0`, no taps, no skew).

---

# 9. Actual vs intended

### A. ACTUAL architecture (only what the code does)

```text
 .iq(+.sigmf-meta) / .wav
 ├─ parser.py: sample_rate REQUIRED, center_frequency ← captures[0] (0.0 for all shipped data), WAV → None
 ↓
 prepare_samples()  ── DC removal, the only pre-ML DSP
 ↓
 classify_samples()  ── CNN softmax {BPSK, QPSK}  ──┐
 ↓                                                  │ argmax
 analyze_signal(modulation=<ML>)  ←─────────────────┘
 ├─ Welch PSD, STFT                      → charts
 ├─ _occupied_bandwidth   ≈ fs          → DISPLAY ONLY (noise-driven)
 ├─ _estimate_snr         P90−P20 gap   → DISPLAY ONLY (+2..+12 dB bias)
 ├─ _estimate_symbol_rate x⁴ peak       → DISPLAY ONLY (often = 4·CFO)
 ├─ _estimate_carrier_offset  Hz, GATED → DISPLAY + DB ONLY  ✗ never reaches recovery
 └─ center = metadata + offset          → DISPLAY (relative labelled as absolute)
 ↓
 build_hypotheses()  ── modulation from ML; interleaving/fec = hardcoded strings, inert
 ↓   (per hypothesis, all K always run)
 run_recovery(samples, hypothesis)
 ├─ synchronize_psk(sps=8 HARDCODED)
 │    ├─ CFO = slope(unwrap(angle(x^order)))/order   2nd, INDEPENDENT estimator, rad/sample, UNGATED
 │    ├─ ✗ polyfit intercept (constant phase) discarded
 │    ├─ integer timing search over range(8); no fractional loop
 │    └─ "Synchronization PASS" == did not raise
 ├─ phase-state search {0,90}° BPSK / {0,90,180,270}° QPSK
 │    └─ selection metric = preamble correlation  ← validation used INSIDE recovery
 ├─ hard-decision demod → 12-row block de-interleave → K=7 rate-½ Viterbi (hard)
 │    └─ each "PASS" == returned without raising
 ↓
 validate_bitstream(threshold 0.90)  ── THE ONLY correctness assertion; score ∈ {0, 1/16, …, 1}
 ↓
 accepted = first PASS          result.validation = accepted else HIGHEST-RANK attempt
 ↓
 SQLite result_json  /  report JSON  /  Analysis·Recovery·Bitstream·Report pages
```

**Data actually flowing from DSP into recovery: the DC-removed samples. Nothing else.**
**Data flowing from ML into DSP: the power-law order for one estimator. Data flowing from ML into recovery: the modulation label.**

### B. INTENDED architecture (per `docs/01-architecture.md`, `02-dsp-pipeline.md`, `05-recovery-chain.md`) — and where reality differs

The documents describe a measurement-first pipeline: *"Before any AI/ML runs, the raw recording is turned into measurable, deterministic characteristics"* ([02:5](file:///e:/Hackathon/SIH2026/main_version1/docs/02-dsp-pipeline.md#L5)), with adaptive synchronization (*"a Costas loop … a timing error detector (e.g. Gardner or Mueller & Müller)"*, [02:39-40](file:///e:/Hackathon/SIH2026/main_version1/docs/02-dsp-pipeline.md#L39-L40)), and validation as an **independent safety net** (*"This is what stops an AI misclassification from silently producing garbage output"*, [01:58](file:///e:/Hackathon/SIH2026/main_version1/docs/01-architecture.md#L58)), with the engine *"passed into the modulation classifier next"* ([02:52](file:///e:/Hackathon/SIH2026/main_version1/docs/02-dsp-pipeline.md#L52)).

Gaps, ranked by how much they change the story:

1. **No loop exists.** Nothing is Costas/Gardner/M&M. Both real estimators are single-shot open-loop fits over the whole record, so `sync.py` is an *estimator*, not a *tracker*. Intended: a closed loop whose lock state is knowable.
2. **The safety net is partly inside the thing it audits.** The preamble is consumed to pick the phase state *before* validation scores it — so the reported correlation is a selection maximum, not an independent confirmation. *Recommendation, not implemented:* restrict the preamble-driven choice to a declared acquisition procedure and score the final verdict on an independent criterion (e.g. Viterbi path metric + CRC-like header check), or hold out part of the frame.
3. **Step statuses carry no information.** Intended `PASS` = "usable output"; actual = "no exception". *Recommendation:* gate `Synchronization` on `timing_metric` and on a residual-CFO bound (both already computed), and report `LOCK/NO LOCK` instead of `PASS`; surface the unused `timing_metric`.
4. **Parameter estimation is aspirational where it overlaps ML.** The docs want center frequency *"estimated as the centroid of the occupied spectrum"* and sample rate *"cross-checked against the Nyquist bandwidth"*, and symbol rate *"from cyclostationary features"* ([02:29-33](file:///e:/Hackathon/SIH2026/main_version1/docs/02-dsp-pipeline.md#L29-L33)) — none of those three mechanisms exists. Only the CFO estimator is genuinely implemented to the documented standard (and it's the best piece of DSP in the repo).
5. **The hypothesis axis is narrower than advertised.** `04-hypothesis-engine.md` describes combining modulation confidence with *candidate* interleaving/FEC pairs; the code has a single candidate each, unused. Either make FEC/interleaving real search dimensions (pass them into `run_recovery`) or stop presenting them as tested hypotheses.

**Already sound — do not change:**
- **ML-before-DSP for estimator selection.** The inversion of the docs' order is *better* than the docs, and the comment explains it. Consider fixing the docs rather than the code.
- **`_estimate_carrier_offset` itself** — mean subtraction to kill the noise-self-mixing DC lump, 8× zero padding, band restriction to `fs/8`, parabolic interpolation, noise-optimal order per class, and the ≥4× **refuse-rather-than-lie** gate. Measured sub-0.5 Hz median error at −2 dB. This is the pattern the other estimators should copy, not a liability.
- **Correlation-gated acceptance as the sole authority + never stopping at the first PASS** ([pipeline.py:20-32](file:///e:/Hackathon/SIH2026/main_version1/backend/pipeline.py#L20-L32)) — testing and visibly refuting the misclassified candidate is the project's differentiating claim and it is genuinely implemented.
- **`backend/` importing nothing from `app/`**, `@dataclass` result objects, and full-`PipelineResult` SQLite round-trip (verified by the `_deserialize` symmetry) — the engine/frontend boundary is real.
- **Coding-layer correctness:** the `(0o171, 0o133)` K=7 terminated trellis, 12-row block permutation inverse, and Gray mapping all satisfy the round-trip property in `tests/test_recovery.py`; they are correct as written.
- The `None`-propagation discipline when `fs` is unknown (`UNAVAILABLE` rather than a bogus Hz figure) — the right instinct, only incomplete.

---

# 10. Final assessment

| Area | What code currently does | Depends on ML? | DSP? | Potential issue |
|---|---|---|---|---|
| **Modulation** | CNN softmax on raw I/Q, mean over ≤32 windows; argmax drives everything | — | no | Confidence never thresholded; only 2 classes, so Top-2 is a permutation |
| **Sample rate** | Metadata passthrough (`core:sample_rate` required; WAV header) | no | no | Never estimated or cross-checked, despite docs claiming so |
| **Bandwidth** | `max−min` of PSD bins above `P20+6 dB` | no | yes | **≈ fs for the whole corpus**; picks noise bins; not a measurement |
| **SNR** | `P90 − P20` of dB-PSD | no | yes | **+2 to +11.6 dB bias**; not an SNR; computed even with unknown `fs` |
| **CFO** | **two** independent estimators: gated spectral (Hz) + ungated phase-slope (rad/sample) | yes (order) | yes | Accurate one is display-only; recovery uses the wrong-by~100 Hz one; **no unit conversion or cross-check anywhere** |
| **Center frequency** | `metadata_center + spectral_offset` | indirectly | yes | Relative baseband shown as absolute; `0.0` indistinguishable from missing; the `absolute_frequency_available` flag is computed then **suppressed by the UI** (and is `True` for a `0.0` placeholder) |
| **Symbol rate** | Peak of `x⁴` periodogram, positive freqs only | no | yes | **Reports 4×CFO or a noise bin**; true 6000 never recovered; result unused by timing |
| **Synchronization** | Open-loop CFO + integer timing search, `sps=8` hardcoded | yes (order) | yes | PASS = didn't raise; `timing_metric` computed and ignored; residual constant phase discarded; no fractional timing |
| **Demodulation** | Hard sign/quadrant decisions after phase-state search | yes (label) | yes | BPSK grid `{0°,90°}` misses the physical 180° flip; hard decisions only; phase chosen via preamble |
| **FEC** | K=7 rate-½ Viterbi, hard decisions, terminated | no | no | PASS = returned; path metric discarded; `hypothesis.fec` never read |
| **Interleaving** | 12-row block inverse | no | no | PASS = reshape succeeded (guaranteed); `hypothesis.interleaving` never read |
| **Validation** | `max correlate(bits,±1 PREAMBLE)/32 ≥ 0.90` | no | no | Only real test, but re-scores an already preamble-maximised candidate; scores quantised to 1/16; fallback picks **highest rank**, not best score |

**1. What does the application actually use ML for?**
Two things, both narrow: (a) the modulation label per hypothesis, which selects the demodulator, the power-law order inside `synchronize_psk`, and the phase-ambiguity grid size; and (b) the power-law order for the *displayed* CFO estimator. Plus a displayed probability bar. ML is not used for FEC, interleaving, CFO values, timing, SNR, bandwidth, symbol rate, or acceptance.

**2. What does it actually use DSP for?**
DC removal; Welch PSD + STFT for charts; four parameter measurements (bandwidth, SNR, symbol rate, CFO) that reach the display/report/DB; and a second, independent DSP block — power-law CFO + integer timing search + hard-decision demodulation — that is the only DSP with authority over the recovered bits.

**3. Does any DSP currently depend on ML output?**
Yes, one parameter and one constant: `_estimate_carrier_offset(..., modulation)` selects orders `(2,)` vs `(4,)`, and `synchronize_psk(..., modulation)` selects `order = 2 or 4` (which also sets the phase-grid size in `chain.py`). Every other DSP function ignores ML entirely.

**4. Is CFO estimated once or multiple times?**
**Twice, independently** — once per run in `analyze_signal`, and again once **per hypothesis** in `synchronize_psk` (so a single analysis performs ≥3 CFO estimates that can all disagree; observed on your file: 62.34 Hz, 123.09 Hz, 21.19 Hz). A third, phase-only mechanism (the π/2 grid) compensates residue without estimating anything.

**5. If multiple, are the estimates connected or independent?**
**Wholly independent.** Different algorithms, units, quality gates, and modulation sources. The gated, sub-Hz-accurate estimate never leaves the display path; the ungated one owns recovery. There is no seeding, no residual correction, no agreement check, and no `rad/sample ↔ Hz` conversion anywhere in the repository. (Empirically, connecting them would change 2 of 64 outcomes on this corpus — so treat this as a correctness/credibility defect, not a proven throughput lever.)

**6. Is the current center-frequency calculation physically/semantically correct?**
**No, as presented — and yes, conditionally, as arithmetic.** `f_c = f_meta + Δf̂` is the right formula for an RF center. But for every shipped capture and every WAV, `f_meta ∈ {0.0, None}` collapses it to a **baseband relative offset** while the UI labels it "center frequency Hz" in an Hz-denominated table; `None` and `0.0` are conflated by `or 0.0`; and the only field that could disambiguate (`absolute_frequency_available`) is both **never rendered** and **wrong by definition** (`True` whenever the key exists, even at `0.0`). Also, `Δf̂` is the peak of the *powered* spectrum without a ±fs/(2·order) ambiguity resolution, so a genuine large offset could alias into the `fs/8` search band.

**7. Is the current recovery architecture internally consistent?**
**Structurally yes, semantically no.** Consistent: the linear order sync→demod→de-interleave→FEC→validate, per-hypothesis isolation, exhaustive hypothesis testing, and a single external acceptance authority. Inconsistent in four specific places: (i) four of five badges assert nothing, yet are styled identically to the one that asserts everything; (ii) the validator's own reference pattern is consumed *inside* recovery for parameter selection, so validation is not independent of the thing it validates; (iii) the pipeline computes a gated, accurate CFO and withholds it from the block that badly needs it, while the block that has an estimate refuses nothing; (iv) two hypotheses report mutually contradictory CFOs for one signal, and `Hypothesis 1`/`Hypothesis 2` differ in *label* only for FEC/interleaving, whose statuses are therefore decorative.

**8. Three most important technical weaknesses**
 1. **Ungated synchronization masquerading as a lock, with a duplicated and discarded estimator.** `synchronize_psk` emits `PASS` plus a CFO it never validates (median error 106 Hz at −2 dB, ~2× truth on your file), while the accurate, refusal-capable estimator sits unused one module away. Fixing this means *one* CFO path: seed recovery from `_estimate_carrier_offset`, and make its `≥4×` gate and the already-computed `timing_metric` decide `LOCK` vs `NO LOCK`. It also means the BPSK phase grid `{0°,180°}` and a retained phase intercept — a residual arbitrary phase makes BPSK `real<0` decisions noise-only, which is precisely the "phase state 1" your panel printed.
 2. **Display-layer overclaiming from uncalibrated measurements.** "Center frequency" (relative → absolute), "Estimated SNR" (+11.6 dB at −2 dB), "Occupied bandwidth" (≈ fs), "Estimated symbol rate" (usually 4×CFO) are shown in one table with equal authority. This is what makes a genuinely impossible −2 dB capture look like an 8.5 dB one that the recovery "failed" — i.e. it manufactures false suspicion about correct rejections. Cheapest high-value fix: render the existing `absolute_frequency_available` flag honestly, gate the bandwidth/SNR/symbol-rate rows with the same refusal discipline the CFO estimator already has, and unit-label CFO as Hz vs rad/sample.
 3. **The chain is structurally brittle in exactly the ways the corpus cannot reveal.** `samples_per_symbol = 8` is hardcoded and never connected to the symbol-rate estimator; timing is integer-only over an assumed grid; decisions are hard; FEC/interleaving are fixed constants dressed as hypothesis dimensions. Every one of these is invisible on generated data (`epsilon=1.0`, taps `[1+0j]`, rectangular `repeat`) and each is a guaranteed failure on a real capture. The Viterbi being a pure-Python double loop executed 4× per hypothesis is also the practical ceiling on raising `top_k` or adding FEC candidates.

**9. What should NOT be changed — already architecturally sound**
 - **Correlation-gated acceptance as the *single* authority, and running every ranked hypothesis instead of stopping at the first PASS.** This is the product's real differentiator and it is implemented, not just documented.
 - **`_estimate_carrier_offset`** — power-law order selection, DC/lump removal, 8× zero padding, band restriction, parabolic interpolation, and above all the **refuse-rather-than-lie** quality gate. It should become the *template* for the rest, not be replaced.
 - **ML-before-DSP hinting** (inverting the docs' order) — a correct engineering decision; update `docs/02-dsp-pipeline.md` instead.
 - **The coding layer** — K=7 (0171, 0133) terminated Viterbi, 12-row block inverse, Gray mapping: all verified correct by round-trip; and the deliberate no-new-dependency choice to hand-roll it.
 - **The engine/UI boundary and persistence design** — no `backend → app` imports, `@dataclass` results, full-`PipelineResult` SQLite round-trip, graceful `None` propagation when `fs` is missing, and honest `UNAVAILABLE` rendering.