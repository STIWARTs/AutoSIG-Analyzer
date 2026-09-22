from __future__ import annotations

import numpy as np

CONSTRAINT_LENGTH = 7
GENERATORS = (0o171, 0o133)
PREAMBLE = np.asarray([int(bit) for bit in "11010011100100011101001110010001"], dtype=np.uint8)
HEADER = np.asarray([int(bit) for bit in "10101010010101011100001100111100"], dtype=np.uint8)


def _parity(value: int) -> int:
    return value.bit_count() & 1


def convolutional_encode(bits: np.ndarray, terminate: bool = True) -> np.ndarray:
    source = np.asarray(bits, dtype=np.uint8)
    if terminate:
        source = np.concatenate((source, np.zeros(CONSTRAINT_LENGTH - 1, dtype=np.uint8)))
    state, output = 0, []
    for bit in source:
        register = (state << 1) | int(bit)
        output.extend(_parity(register & polynomial) for polynomial in GENERATORS)
        state = register & ((1 << (CONSTRAINT_LENGTH - 1)) - 1)
    return np.asarray(output, dtype=np.uint8)


def viterbi_decode(received: np.ndarray, terminated: bool = True) -> np.ndarray:
    data = np.asarray(received, dtype=np.uint8)
    if len(data) % 2:
        data = data[:-1]
    states = 1 << (CONSTRAINT_LENGTH - 1)
    metrics = np.full(states, np.inf)
    metrics[0] = 0.0
    history: list[np.ndarray] = []
    for pair in data.reshape(-1, 2):
        next_metrics = np.full(states, np.inf)
        choices = np.zeros(states, dtype=np.int16)
        for state in range(states):
            if not np.isfinite(metrics[state]):
                continue
            for bit in (0, 1):
                register = (state << 1) | bit
                expected = np.asarray([_parity(register & poly) for poly in GENERATORS])
                next_state = register & (states - 1)
                candidate = metrics[state] + np.count_nonzero(expected != pair)
                if candidate < next_metrics[next_state]:
                    next_metrics[next_state] = candidate
                    choices[next_state] = (state << 1) | bit
        metrics, history = next_metrics, history + [choices]
    state = 0 if terminated and np.isfinite(metrics[0]) else int(np.argmin(metrics))
    decoded = []
    for choices in reversed(history):
        choice = int(choices[state])
        decoded.append(choice & 1)
        state = choice >> 1
    decoded = np.asarray(decoded[::-1], dtype=np.uint8)
    return decoded[: -(CONSTRAINT_LENGTH - 1)] if terminated else decoded


def block_interleave(bits: np.ndarray, rows: int = 12) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8)
    if len(values) % rows:
        raise ValueError(f"Block interleaver needs a length divisible by {rows}; got {len(values)}")
    return values.reshape(rows, -1).T.reshape(-1)


def block_deinterleave(bits: np.ndarray, rows: int = 12) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8)
    if len(values) % rows:
        raise ValueError(f"Block de-interleaver needs a length divisible by {rows}; got {len(values)}")
    return values.reshape(-1, rows).T.reshape(-1)


def make_frame(payload: np.ndarray) -> np.ndarray:
    return np.concatenate((PREAMBLE, HEADER, np.asarray(payload, dtype=np.uint8)))
