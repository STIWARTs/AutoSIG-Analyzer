# Project Structure

Actual layout of the repository as shipped (every entry below exists today; nothing here is aspirational).

```
SIH/
│
├── app/                         # Streamlit frontend — the only runtime UI
│   ├── streamlit_app.py         # entry point: upload screen, nav, run/persist orchestration
│   ├── pages/
│   │   ├── dashboard.py         # active-analysis panel + SQLite history list
│   │   ├── analysis.py          # spectrum, waterfall, parameters, raw constellation
│   │   ├── recovery.py          # Top-K hypotheses, live per-step pass/fail chain
│   │   ├── bitstream.py         # preamble-confirmed recovered bits, header/payload view
│   │   └── report.py            # human-readable + machine-readable report
│   └── components/
│       ├── widgets.py           # status badges (incl. WARN/NO LOCK), instrument panels
│       └── charts.py            # Plotly plot wrappers, theme-adaptive
│
├── backend/                     # all product logic; never imports from app/
│   ├── pipeline.py              # orchestration: ingest → ML classify → DSP → hypotheses
│   │                            #   → recovery → validation; picks best attempt as fallback view
│   ├── types.py                 # shared dataclasses (IngestedSignal, AnalysisResult,
│   │                            #   RecoveryAttempt, ValidationResult, …)
│   ├── ingestion/
│   │   └── parser.py            # .iq (+SigMF) and .wav parsers → unified complex samples
│   ├── dsp/
│   │   ├── analysis.py          # Welch PSD, STFT waterfall, parameter estimation
│   │   ├── carrier.py           # shared quality-gated CFO estimator (≥4× band-mean gate;
│   │   │                        #   refuses → None, never coerced to 0 Hz) — used by BOTH
│   │   │                        #   display and synchronization, so they cannot disagree
│   │   └── sync.py              # synchronize_psk: CFO correction + concentration-metric
│   │                            #   timing phase; locked=False only on estimator refusal
│   ├── ml/
│   │   └── classifier.py        # trained I/Q CNN inference only (softmax → hypothesis ranks)
│   ├── hypotheses/
│   │   └── engine.py            # Top-K engine — modulation is the only hypothesized dimension
│   ├── recovery/
│   │   ├── chain.py             # per-hypothesis recovery: sync → demod (discrete phase-state
│   │   │                        #   search) → de-interleave → Viterbi; step-by-step audit trail
│   │   └── coding.py            # frame/PREAMBLE+HEADER construction, block interleaver,
│   │                            #   rate-½ K=7 convolutional encode + terminated Viterbi decode
│   ├── validation/
│   │   └── correlation.py       # acceptance gate: ±1 correlation of the known 32-bit PREAMBLE
│   │                            #   in recovered bits vs 0.90 threshold — evidences framing,
│   │                            #   does NOT prove payload correctness (see docs/06)
│   ├── correlation/             # empty placeholder package; correlation landed in
│   │                            #   backend/validation/ — nothing imports this stub
│   ├── storage/
│   │   └── history.py           # SQLite persistence via stdlib sqlite3 (no external DB)
│   ├── reports/
│   │   └── generator.py         # structured report JSON/markdown for the Report page
│   └── eval/                    # OFFLINE ground-truth evaluation core — never imported by the
│       ├── ground_truth.py      #   running app: deterministic seeded replay of the corpus
│       │                        #   (bit-identity integrity gate against datasets/*.iq)
│       └── payload_metrics.py   #   payload anchoring + micro/macro BER outcome ladder
│
├── tools/                       # offline verification & audit harnesses (import backend, not app)
│   ├── cfo_ab_report.py         # corpus ground-truth A/B harness for CFO estimator changes
│   ├── cfo_ab_show.py           # pretty-printer for the A/B JSONs
│   ├── _cfo_diff.py             # per-file pass-regression pinpointing
│   ├── _screen_spotcheck.py     # headless Streamlit AppTest exception sweep
│   ├── cfo_ab_baseline.json     # committed legacy-polyfit reference numbers
│   ├── cfo_ab_after.json        # committed unified-estimator reference numbers
│   ├── corpus_payload_eval.py   # Step-3 evaluator: payload ground truth over all 64 captures
│   ├── corpus_payload_report.json  # committed result record (micro-BER baseline)
│   ├── failure_forensics.py     # Step-4 stage-by-stage failure attribution (read-only)
│   ├── failure_forensics.json   # committed forensic results
│   └── *.md                     # audit records: AUDIT.md, BitRecoveryAUDIT.md,
│                                #   GroundTruthAUDIT.md, Offline-Payload audit, failure-forensics audit
│
├── training/                    # offline data/model production (not run at app runtime)
│   ├── generate_dataset.py      # corpus generator: GNU Radio flowgraph when runnable, else
│   │                            #   the explicitly labeled NumPy flowgraph-equivalent fallback
│   │                            #   (shipped datasets/ came from the fallback; every manifest
│   │                            #   record and .sigmf-meta description says so)
│   └── train_classifier.py      # trains models/modulation_cnn.pt + measured metrics JSON
│
├── models/                      # artifacts loaded at runtime
│   ├── modulation_cnn.pt        # trained two-class (BPSK/QPSK) CNN weights
│   └── modulation_cnn.metrics.json  # measured test metrics shipped alongside the model
│
├── datasets/                    # 64 synthetic captures × (.iq + .sigmf-meta + .wav) + manifest.json
│                                #   (gitignored — regenerable via training/generate_dataset.py
│                                #    from the recorded seed; ground truth lives in manifest.json)
│
├── gnuradio/                    # GNU Radio flowgraph definition + README (see provenance note above)
├── data/                        # runtime artifacts: autosig.db SQLite analysis history (seeded with
│                                #   real demo runs and committed; delete to reset history)
│
├── tests/                       # pytest suite (12 tests): recovery-chain units + ground-truth
│   ├── test_recovery.py         #   replay/integrity-gate lock-in
│   └── test_payload_eval.py
│
├── docs/                        # this specification folder
│   ├── 00…15-*.md               # numbered design docs (overview → stage-1 issues & stage-2 plan)
│   ├── design.md                # original design narrative
│   ├── model-training.md        # data provenance + training recipe + metrics
│   ├── README.md                # doc index
│   └── screenshots/             # demo-flow screenshots used by docs/README and README.md
│
├── .streamlit/config.toml       # Streamlit theme/server config for local run
├── .conda/                      # project-local Conda environment (not shipped to users)
├── .devcontainer/devcontainer.json
├── .gitignore                   # ignores datasets/, .conda/, __pycache__, etc.
├── .python-version
├── requirements.txt
└── README.md
```

## Notes

- No `desktop/` folder exists at this stage — the C#/WPF desktop client is a future-stage concern and is not scaffolded.
- `backend/` never imports anything from `app/`, so it stays reusable behind a future different frontend; `app/` only imports `backend`.
- `backend/eval/` and `tools/` are the offline verification surface: they import `backend`, but the running application never imports them. They are what make payload-correctness and CFO-accuracy claims measured rather than asserted.
- `training/` is run manually/offline to produce files in `models/` and `datasets/`; it is not invoked by the running Streamlit app.
- `backend/storage/` persists every completed analysis (preamble-confirmed or all-failed) to `data/autosig.db` using only the standard-library `sqlite3` module — no external DB server, no extra dependency.
- `datasets/` is gitignored by design: the corpus is fully reproducible from the recorded seed, and the evaluation tooling re-verifies bit-identity of the on-disk files against that replay before trusting any metric.
- `backend/correlation/` is an empty placeholder left from initial scaffolding — the correlation logic lives in `backend/validation/correlation.py`. It is referenced by nothing and can be deleted in any future pass without consequence.
