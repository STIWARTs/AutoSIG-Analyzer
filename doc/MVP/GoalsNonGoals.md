# Goals, Non-Goals, Assumptions and Boundaries

## 2.1 Primary goals

1. Accept `.IQ` and `.wav` recordings.
2. Validate and normalize input.
3. Automatically detect signal regions.
4. Provide signal visualization.
5. Extract physical signal parameters.
6. Classify modulation.
7. Generate FEC/interleaving candidates.
8. Demodulate supported modulation families.
9. De-interleave supported schemes.
10. Decode supported FEC families.
11. Validate candidate recovery.
12. Correlate recovered bits.
13. Identify likely headers/payload boundaries.
14. Generate an auditable final report.

## 2.2 Non-goals

The project should not claim:

- universal protocol identification
- guaranteed identification of arbitrary FEC/interleaving
- guaranteed recovery from severely damaged recordings
- cryptographic decryption
- semantic interpretation of encrypted payloads
- perfect performance on every sensor/file format
- that ML replaces DSP

Use **payload format parsing** rather than "decryption" in the architecture.

## 2.3 Important assumptions

- Training labels are available for supervised models through controlled synthetic generation and/or curated datasets.
- GNU Radio can generate known-ground-truth signals for the initial training set.
- Input files are recordings of digitally sampled signals.
- Some metadata may be absent.
- Real recordings may contain noise, frequency offset, timing offset and impairments.
- Some signal configurations will remain unknown or unsupported.

## 2.4 Demo scope principle

The architecture is generalized, but the SIH prototype should validate a small number of complete end-to-end paths.

Recommended first vertical slice:

```text
QPSK
+
Convolutional coding
+
One interleaver
+
Soft/hard Viterbi decoding
+
Bit correlation
+
Report
```

Then add additional combinations.

## 2.5 Output confidence

Every automated conclusion should carry:

- confidence
- evidence/features
- validation result
- processing status

Possible terminal states:

- `SUCCESS`
- `LOW_CONFIDENCE`
- `UNCLASSIFIED`
- `UNSUPPORTED`
- `INVALID_INPUT`
- `PROCESSING_ERROR`

Never silently convert failure into a guessed result.
