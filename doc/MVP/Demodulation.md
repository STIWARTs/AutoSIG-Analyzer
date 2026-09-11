# 9. Demodulation

## 9.1 Role

Demodulation converts a synchronized waveform into symbols/bits according to a modulation hypothesis.

The PS explicitly asks for:

- FSK
- PSK
- QAM

## 9.2 FSK

Conceptually:

```text
frequency state
 ↓
frequency discriminator / detector
 ↓
symbol decisions
 ↓
bits
```

Useful supporting measurements:

- instantaneous frequency
- tone separation
- symbol timing

## 9.3 PSK

For PSK:

```text
IQ samples
 ↓
matched filtering
 ↓
timing recovery
 ↓
carrier/phase recovery
 ↓
symbol decisions
 ↓
bit mapping
```

Start with QPSK for the MVP.

## 9.4 QAM

QAM uses amplitude and phase.

```text
IQ
 ↓
synchronization
 ↓
equalization where needed
 ↓
constellation decision
 ↓
Gray mapping where configured
 ↓
bits
```

Support should be parameterized by constellation order.

## 9.5 Hard vs soft decisions

Hard:

```text
symbol → 0/1
```

Soft:

```text
symbol → confidence/reliability information
```

Soft information is especially valuable for FEC decoders that support soft-input decoding.

## 9.6 Demodulator contract

Input:

```text
samples
sample_rate
symbol_rate
carrier_offset
modulation
configuration
```

Output:

```text
soft_bits or hard_bits
symbol_metrics
sync_metrics
quality metrics
errors
```

## 9.7 Important limitation

A constellation that looks like QPSK does not by itself prove the entire signal configuration.

It only supports a hypothesis. The downstream recovery and validation stages provide stronger evidence.
