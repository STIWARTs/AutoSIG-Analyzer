# Modulation Classification

## Purpose

This is the one place in the pipeline where a learned model, rather than deterministic signal processing, is used — and its job is narrow and specific: given the complex I/Q samples (or a windowed segment of them), output a probability for each candidate modulation class. It does not decide interleaving or FEC, and it does not get to make an unchecked final call; its output feeds the Hypothesis Engine, and every one of its predictions is later checked against real decoding and correlation results (`06-validation-correlation.md`).

## Approach

A convolutional neural network trained directly on raw I/Q sample windows is the established approach in this space — classifying modulation from a windowed sequence of I/Q pairs using a CNN is a standard, well-published technique in the automatic modulation classification (AMC) literature, not a novel or risky choice for this project. See `14-references.md` for the specific papers this approach is grounded in.

- **Input:** a fixed-length window of complex samples, represented as a 2×N array (I channel, Q channel) or as a single complex-valued array depending on the framework.
- **Output:** a softmax probability distribution over the modulation classes the model was trained on.
- **Model:** a small CNN (a few convolutional layers over the I/Q sequence, followed by fully connected layers and a softmax) is sufficient for the MVP's class count and is fast enough to run in a Streamlit app without a GPU.

## MVP Class Scope

To keep the prototype demonstrable and reliable, the MVP classifier is trained on a small, deliberately bounded set of classes:

- **QPSK**
- **BPSK**

Expanding to FSK, 8PSK, and QAM variants is explicitly a Stage 2 item (`12-mvp-scope.md`) — adding classes here is cheap in code but expensive in the amount of labeled training data and validation time needed to trust the result, so it is deferred rather than rushed.

## Training Data

The classifier is trained entirely on the synthetic dataset described in `07-data-generation.md` — captures produced by a NumPy implementation of the repo's GNU Radio flowgraph (which was not runnable in this environment), with known ground-truth modulation, at a range of SNR levels and small frequency offsets, so the model learns to be robust to noise and imperfect synchronization rather than only recognizing clean textbook signals.

## Libraries

`PyTorch` (or `scikit-learn` for a simpler baseline classifier if time is short) for model definition and training; `NumPy` for data handling. Training happens offline (in `training/`), and only the trained model weights are loaded at runtime by the Streamlit app — the app itself does not train anything live.

## Output of This Stage

A dictionary mapping each candidate modulation class to a confidence score, e.g. `{"QPSK": 0.82, "BPSK": 0.14, ...}`. This is passed directly into the Hypothesis Engine.
