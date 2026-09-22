# File Format Handling: .IQ and .WAV

## Why This Needs Its Own Specification

The PS requires support for both `.IQ` and `.wav` input, and these are fundamentally different file formats with different ambiguities. Treating them as interchangeable inputs to one generic parser is a mistake — each needs its own parsing path, and both must converge on the same internal representation before the rest of the pipeline touches them.

## `.IQ` Files

A raw `.IQ` file is just a sequence of bytes — there is no header, so nothing about sample rate, center frequency, or the exact numeric format (e.g. `int16` interleaved I/Q, or `complex64`) can be recovered from the file alone. SigMF is the preferred path: users can upload one or more files together and AutoSIG automatically pairs `signal_01.iq` with `signal_01.sigmf-meta` by their shared filename stem. The parser then reads the sidecar's datatype, sample rate, and capture parameters to interpret the raw bytes correctly.

When a matching SigMF sidecar is not available, the Upload screen provides an inline metadata form. The analyst may supply a required-for-absolute-analysis sample rate, an optional center frequency, and a datatype (default `cf32_le`). If no sample rate is supplied, AutoSIG still accepts the capture and runs only relative/normalized spectral and constellation analysis plus modulation classification. It never fabricates a sample rate: bandwidth in Hz, symbol rate in baud, and center frequency in Hz are explicitly marked unavailable until a trustworthy rate is provided.

## `.WAV` Files

WAV is a standard PCM audio container, and it is used in two different ways in this domain, which the parser must distinguish:

- **Mono WAV** — treated as a real-valued baseband or audio-range signal.
- **Stereo WAV** — treated using the common SDR convention where the left channel carries the I component and the right channel carries the Q component, reconstructing a complex signal exactly as `.IQ` would represent it.

The WAV header itself supplies the sample rate directly (unlike raw `.IQ`, WAV is a self-describing format), which is read via `scipy.io.wavfile` or the `soundfile` library.

## Unified Internal Representation

Regardless of which file type was uploaded, ingestion produces the same structure for the rest of the pipeline to consume:

```python
{
    "samples": np.ndarray,       # complex-valued sample array
    "sample_rate": float | None, # Hz; None when raw IQ metadata is unavailable
    "center_frequency": float,   # Hz, if known; None otherwise
    "source_format": "iq" | "wav",
}
```

Every later pipeline stage (`02-dsp-pipeline.md` onward) operates only on this structure and never needs to know which original file format it came from.
