# MVP Scope and Staged Roadmap

Being explicit about what is and is not in the prototype is itself part of the project's credibility — it shows the judges a team that understands the full PS but has made a deliberate, defensible scoping decision for a time-boxed prototype, rather than a team that either overpromises or has simply not thought about the rest of the problem statement.

## Stage 1 — Working MVP (this prototype)

- Input: `.IQ` and `.WAV`.
- DSP analysis: full (spectrum, waterfall, raw-vs-recovered constellation, parameter estimation, synchronization).
- Modulation identification: QPSK and BPSK only.
- Top-K hypothesis generation: yes, bounded to the Stage 1 candidate lists below. In practice this means **modulation is the only hypothesized, varying dimension**.
- Demodulation supported in recovery: **QPSK and BPSK** (both fully demodulated; acceptance is decided by preamble correlation, which evidences frame structure, not per-bit payload correctness).
- Interleaving supported in recovery: **Block** only — a *fixed recovery configuration*, identical for every hypothesis, not a searched or independently tested dimension.
- FEC supported in recovery: **Convolutional code with Viterbi decoding** only — likewise fixed for every hypothesis (MVP scope).
- Bitstream correlation / header-payload identification: full, working.
- Report generation: full, working.
- Analysis history: full, working — every completed run (preamble-confirmed or all-failed) is persisted to a standard-library SQLite database (`data/autosig.db`) and replayable from the Dashboard, surviving server restarts with no external DB dependency.

## Stage 2 — Expandable Modules (post-MVP, if time allows)

- Additional modulations: FSK, additional PSK/QAM orders.
- Additional interleaving: Convolutional, Diagonal, Pseudo-Random.
- Additional FEC: Reed-Solomon, LDPC, concatenated codes.

The architecture (Hypothesis Engine, Recovery Chain, Validation) is already designed to accept these as additional candidate entries without redesign — Stage 2 is about adding candidate implementations, not restructuring the pipeline.

## Stage 3 — Future Scale (post-hackathon)

- Real-time SDR input (rather than only pre-recorded files).
- GPU-accelerated inference for the modulation classifier.
- Broader protocol/signal support.
- Migration of the frontend to the React + FastAPI or native desktop architecture discussed in `09-tech-stack.md`, reusing the same Python backend.

## Key Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Limited labeled real-world signals | Use synthetic datasets with known ground truth — the GNU Radio flowgraph or, as shipped, its explicitly labeled NumPy equivalent (`07-data-generation.md`) |
| Multiple possible decoding configurations | Top-K hypothesis ranking bounds the search (`04-hypothesis-engine.md`) |
| Incorrect AI/ML prediction | Every prediction is tested through real DSP recovery and preamble correlation, not trusted directly — acceptance requires detecting the known preamble, so a misclassification is visibly refuted rather than silently reported (`06-validation-correlation.md`) — this is the project's core differentiator, not just a risk mitigation |
| Noise and signal impairments | Train and test across multiple SNR levels and frequency offsets |
| High computational complexity | Bounded Top-K candidates plus a limited retry mechanism |
| Large IQ/WAV recordings | Signal segmentation and chunk-based processing |
