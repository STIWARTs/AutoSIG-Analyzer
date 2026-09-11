# IQ and WAV Input Handling

## 8.1 IQ data

IQ commonly means two components:

```text
I = in-phase
Q = quadrature
```

A complex sample can be represented as:

```text
x[n] = I[n] + jQ[n]
```

IQ files may be:

- interleaved I/Q
- separate I and Q streams
- integer samples
- floating-point samples
- little/big endian depending on format
- accompanied by external metadata

Never assume a raw IQ file has a universal format.

## 8.2 WAV

WAV is a container format.

Its samples may represent:

- real-valued samples
- one channel
- multiple channels
- potentially I/Q stored as two channels depending on acquisition/export conventions

Therefore the parser must inspect:

- sample width
- sample rate
- channel count
- encoding
- duration
- numeric range

Do not state that every WAV file is RF passband or every WAV is baseband.

## 8.3 File validation

Validate:

- extension
- magic/header where applicable
- file size
- sample count
- channel count
- sample format
- numeric finiteness
- metadata consistency
- truncation/corruption

## 8.4 Large files

Use:

- chunked reading
- memory mapping where applicable
- streaming analysis
- segment-level processing

Do not load multi-gigabyte recordings into RAM unnecessarily.

## 8.5 Canonical internal representation

Convert supported inputs into an internal representation such as:

```text
Complex64/Complex128 array
+
sample_rate
+
center_frequency if available
+
channel metadata
+
time origin
+
source metadata
```

This allows downstream DSP to be format-independent.

## 8.6 Metadata precedence

Recommended precedence:

```text
trusted file metadata
        ↓
explicit user-provided metadata
        ↓
external acquisition metadata
        ↓
DSP estimation
        ↓
unknown
```

The exact precedence should be defined in configuration.

## 8.7 Input status

Possible states:

- VALID
- VALID_WITH_MISSING_METADATA
- CORRUPT
- UNSUPPORTED_FORMAT
- EMPTY
- INSUFFICIENT_SIGNAL
