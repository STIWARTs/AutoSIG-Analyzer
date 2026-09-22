# Deployment and Demo Checklist

## Deployment

1. Push the repository to GitHub, following the structure in `10-project-structure.md`.
2. Deploy `app/streamlit_app.py` via Streamlit Community Cloud, pointing it at the GitHub repo. This produces a public URL of the form `https://autosig-xxxxx.streamlit.app`.
3. Confirm the deployed app can actually load a sample `.iq`/`.sigmf-meta` pair and a sample `.wav` from `datasets/` and complete the full pipeline without errors — test this from a fresh browser session, not just locally.
4. Put the resulting URL into the submission PPT.

## Demo Video Script

The video should let the working pipeline carry the narrative rather than narrating the architecture verbally. Suggested sequence, using one of the known synthetic files from `datasets/`:

1. Open the deployed URL and upload a synthetic `.iq` file live.
2. Show the Analysis screen populate: spectrum, waterfall, constellation, and the extracted parameters (sample rate, bandwidth, SNR, symbol rate).
3. Show the modulation classifier's confidence scores.
4. Show the Top-K hypothesis list.
5. Show Hypothesis #1 running through synchronization, demodulation, de-interleaving, and FEC decoding, then failing frame validation.
6. Show the system automatically move to Hypothesis #2, and pass validation.
7. Show the recovered bitstream with the header/payload split and correlation score.
8. Show the generated report, and (optionally) its download.

Keep the whole sequence tight — the goal is to demonstrate the hypothesis → recovery → validation → next-hypothesis loop clearly, since that loop is the project's central technical claim, not to narrate every architectural decision.

## Before Recording

- Re-run the exact demo file through the deployed (not local) app at least once beforehand to catch any deployment-specific issues.
- Have a second, different synthetic file ready as a backup in case the first one behaves unexpectedly during recording.
