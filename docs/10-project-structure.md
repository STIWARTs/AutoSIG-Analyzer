# Project Structure

```
SIH-26147/
│
├── app/
│   ├── streamlit_app.py        # entry point
│   ├── pages/
│   │   ├── dashboard.py
│   │   ├── analysis.py         # spectrum, waterfall, parameters
│   │   ├── recovery.py         # hypothesis list, live pass/fail
│   │   ├── bitstream.py        # header/payload view
│   │   └── report.py
│   └── components/             # shared UI widgets (status badges, plot wrappers)
│
├── backend/
│   ├── ingestion/               # .iq / .wav parsers → unified sample representation
│   ├── dsp/                     # FFT/PSD, spectrogram, parameter estimation, sync
│   ├── ml/                      # modulation classifier (inference only)
│   ├── hypotheses/               # Top-K hypothesis engine
│   ├── recovery/                 # demodulation, de-interleaving, FEC decoding
│   ├── validation/                # bitstream correlation, header/payload split
│   ├── correlation/                # (may be merged into validation/)
│   ├── storage/                    # SQLite analysis history (stdlib sqlite3, no server)
│   └── reports/                    # report generation
│
├── training/                    # offline model training scripts (not run at app runtime)
├── models/                      # trained model weights loaded by backend/ml
├── datasets/                    # synthetic .iq + .sigmf-meta + .wav files, ground truth labels
├── gnuradio/                    # GNU Radio flowgraph definition (shipped datasets/ came from its labeled NumPy fallback)
├── data/                        # runtime artifacts: autosig.db SQLite analysis history (created on first run)
├── tests/                       # unit tests for backend components
├── docs/                        # this specification folder
├── requirements.txt
└── README.md
```

## Notes

- No `desktop/` folder exists at this stage — the C#/WPF desktop client is a future-stage concern and should not be scaffolded now.
- `backend/` must not import anything from `app/`, so it stays reusable behind a future different frontend.
- `training/` is run manually/offline to produce files in `models/`; it is not invoked by the running Streamlit app.
- `backend/storage/` persists every completed analysis to `data/autosig.db` with the standard-library `sqlite3` module (no external DB server, no extra dependency); `data/` is created on first run and holds runtime artifacts only, so it is safe to delete to reset history.
