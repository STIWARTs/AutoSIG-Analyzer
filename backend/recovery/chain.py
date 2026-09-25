from __future__ import annotations

import numpy as np

from backend.dsp.sync import synchronize_psk
from backend.recovery.coding import block_deinterleave, viterbi_decode
from backend.types import Hypothesis, RecoveryAttempt
from backend.validation.correlation import validate_bitstream


def _qpsk_demodulate(symbols: np.ndarray) -> np.ndarray:
    # Gray mapping: 00 -> (+,+), 01 -> (-,+), 11 -> (-,-), 10 -> (+,-)
    real_negative = (symbols.real < 0).astype(np.uint8)
    imag_negative = (symbols.imag < 0).astype(np.uint8)
    return np.column_stack((real_negative, real_negative ^ imag_negative)).reshape(-1)


def _bpsk_demodulate(symbols: np.ndarray) -> np.ndarray:
    return (symbols.real < 0).astype(np.uint8)


def run_recovery(samples: np.ndarray, hypothesis: Hypothesis, samples_per_symbol: int = 8) -> RecoveryAttempt:
    steps: list[tuple[str, str, str]] = []
    if hypothesis.modulation not in ("QPSK", "BPSK"):
        return RecoveryAttempt(hypothesis, [("Synchronization", "FAIL", "Unsupported modulation")],
                               error="Unsupported recovery modulation")
    try:
        symbols, sync = synchronize_psk(samples, samples_per_symbol, hypothesis.modulation)
        if sync["locked"]:
            steps.append(("Synchronization", "PASS", f"CFO {sync['cfo_rad_per_sample']:.5f} rad/sample"))
        else:
            # Shared estimator refused to lock: NO LOCK/LOW CONFIDENCE, frequency
            # correction was skipped (not zeroed), and recovery proceeds so Frame
            # Validation remains the final evidence gate.
            steps.append(("Synchronization", "WARN", "NO LOCK \u2014 CFO estimate refused; continuing uncorrected"))
        # A fourth-power Costas-style estimator determines CFO but leaves phase
        # ambiguity (90-degree for QPSK, 180-degree for BPSK). Resolve those
        # physical carrier states against the known sync word, then let
        # validation independently apply the acceptance threshold below the
        # recovery chain.
        demodulate = _qpsk_demodulate if hypothesis.modulation == "QPSK" else _bpsk_demodulate
        # QPSK has a four-quadrant (90-degree) ambiguity; BPSK's physical
        # ambiguity is a 180-degree flip, so its grid must not spend a slot on
        # a 90-degree rotation that only scrambles the decision boundary.
        phase_angles = ([0.0, np.pi / 2, np.pi, 3 * np.pi / 2] if hypothesis.modulation == "QPSK"
                        else [0.0, np.pi])
        candidates: list[tuple[float, np.ndarray, int]] = []
        n_bits = len(symbols) * (2 if hypothesis.modulation == "QPSK" else 1)
        for phase_index, angle in enumerate(phase_angles):
            rotated = symbols * np.exp(-1j * angle)
            hard_bits = demodulate(rotated)
            # Keep the largest block the 12-row interleaver accepts (and an even
            # count for the rate-1/2 code); a residual tail is standard to drop.
            block = len(hard_bits) - len(hard_bits) % 12
            hard_bits = hard_bits[: block - (block % 2)]
            decoded_candidate = viterbi_decode(block_deinterleave(hard_bits), terminated=True)
            candidates.append((validate_bitstream(decoded_candidate, threshold=-1).correlation_score,
                               decoded_candidate, phase_index))
        _, decoded, phase_index = max(candidates, key=lambda item: item[0])
        phase_state_degrees = float(np.degrees(phase_angles[phase_index]))
        # Re-derive the winning carrier state so we can expose the exact
        # post-synchronization symbol cloud (timing + CFO + phase corrected)
        # that demodulation turned into bits, for the recovered constellation.
        synchronized_symbols = symbols * np.exp(-1j * phase_angles[phase_index])
        tail = ""
        block = n_bits - n_bits % 12
        if block - (block % 2) < n_bits:
            tail = f"; {n_bits - (block - (block % 2))} tail bits dropped"
        steps.append((f"{hypothesis.modulation} Demodulation", "PASS",
                      f"{n_bits} hard bits; phase state {phase_state_degrees:.0f}°{tail}"))
        steps.append(("Block De-interleaving", "PASS", "12-row block inverse"))
        steps.append(("Viterbi FEC", "PASS", f"{len(decoded)} decoded bits"))
        return RecoveryAttempt(hypothesis, steps, decoded, synchronized_symbols=synchronized_symbols,
                               phase_state_degrees=phase_state_degrees)
    except Exception as exc:
        steps.append(("Recovery", "FAIL", str(exc)))
        return RecoveryAttempt(hypothesis, steps, error=str(exc))
