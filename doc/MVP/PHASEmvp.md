# 11. Bitstream, Correlation, Header/Payload and Reporting

## 11.1 Bitstream processing

After FEC:

```text
decoded bits
 ↓
optional descrambling only when configuration is known
 ↓
bit packing/unpacking
 ↓
frame synchronization
```

Avoid implying cryptographic decryption.

## 11.2 Bit-stream correlation

Correlation can identify known structures such as:

- preambles
- synchronization sequences
- known test patterns
- candidate headers

Conceptually:

```text
Recovered bits
      +
Known sequence
      ↓
Correlation
      ↓
peaks
      ↓
candidate frame boundaries
```

## 11.3 Header/payload identification

If a protocol is known:

```text
frame
 ↓
header length/schema
 ↓
payload
```

If protocol is unknown:

```text
candidate header region
+
statistical/structural evidence
+
correlation
 ↓
estimated boundary
```

Label uncertain results as estimates.

## 11.4 Final report

Recommended report sections:

### Input

- file name
- format
- file size
- duration
- sample format
- channels
- sample rate
- center frequency if available

### Estimated parameters

- bandwidth
- symbol rate
- SNR
- frequency offset
- modulation
- FEC
- interleaving
- confidence

### Evidence

- spectrum
- waterfall
- constellation
- eye diagram
- parameter plots

### Recovery

- selected hypothesis
- demodulator
- interleaver
- FEC
- decoder metrics
- validation result

### Bit analysis

- correlation peaks
- preamble
- frame boundaries
- header
- payload

### Audit

- pipeline stages
- timings
- model version
- configuration
- warnings/errors

## 11.5 Export formats

Recommended:

- PDF — human-readable report
- JSON — machine-readable complete result
- CSV — tabular parameters/metrics
- PNG — visual plots
- TXT/BIN — recovered bitstream where appropriate
- log — processing trace
