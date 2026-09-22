# Technology Stack

## Decision: Streamlit + Python, Not React/FastAPI or Desktop C#/WPF

This decision was made deliberately for the current project stage — a working prototype that must be demonstrated via a video and a URL link in the submission PPT, not the eventual production system.

- **Why not desktop (C#/WPF)?** A desktop application cannot be linked as a URL for judges to open, and building a native GUI alongside the actual signal-processing engine would consume time better spent making the DSP/ML pipeline itself correct. Desktop remains the intended path for a future, post-hackathon product, with the Python backend reused underneath it.
- **Why not React + FastAPI for the prototype?** It is architecturally the stronger long-term choice and remains the intended path if this project continues past the hackathon, but it requires building and deploying two separate stacks (frontend and API) under time pressure, which risks leaving less time for the part that is actually judged: whether the hypothesis-driven recovery pipeline genuinely works. Streamlit collapses UI and backend wiring into one lightweight layer, which is the right trade for a time-boxed prototype.
- **Why Streamlit works for AutoSIG specifically:** the application is fundamentally "upload a file → run Python signal processing and ML → show plots and results," which is exactly what Streamlit is built for, with minimal custom frontend code required.

## Stack

- **Frontend / App Layer:** Streamlit (Python).
- **Signal Processing:** NumPy, SciPy (FFT, filtering, resampling, spectral estimation); GNU Radio (synthetic dataset generation, and any DSP block better sourced from an existing, tested implementation than hand-rolled).
- **Machine Learning:** PyTorch (or scikit-learn for a lighter baseline) for the modulation classifier; trained offline, loaded at runtime.
- **Metadata Standard:** SigMF for `.IQ` file metadata.
- **Visualization:** Plotly or Matplotlib for spectrum, waterfall, and constellation plots inside Streamlit.
- **Version Control / Hosting:** GitHub repository; deployed via Streamlit Community Cloud for a public URL.

## Explicit Non-Goals for This Stage

Real-time SDR input, GPU acceleration, and a native desktop GUI are all explicitly out of scope for the prototype and belong to later stages (`12-mvp-scope.md`).
