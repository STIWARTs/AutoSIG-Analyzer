"""GNU Radio flowgraph for writing impaired, oversampled PSK I/Q captures.

The framing/FEC/interleaving bits are prepared in Python; GNU Radio performs the
actual symbol expansion, frequency offset, AWGN channel, and complex file sink.
"""
from __future__ import annotations

import math
from pathlib import Path
import numpy as np


def run_flowgraph(symbols: np.ndarray, output_path: str | Path, sample_rate: float, samples_per_symbol: int,
                  frequency_offset_hz: float, snr_db: float) -> str:
    """Run the GNU Radio graph; retain an explicitly labelled offline fallback.

    The fallback follows the same repeat → rotator → AWGN stages so development
    remains possible on Windows builds without a current GNU Radio wheel.
    """
    try:
        from gnuradio import analog, blocks, channels, gr  # Installed only for offline dataset generation.
    except ImportError:
        repeated = np.repeat(np.asarray(symbols, dtype=np.complex64), samples_per_symbol)
        phase = 2 * np.pi * frequency_offset_hz * np.arange(len(repeated)) / sample_rate
        rotated = repeated * np.exp(1j * phase)
        sigma = np.sqrt(np.mean(np.abs(repeated) ** 2) / (2 * 10 ** (snr_db / 10)))
        impaired = rotated + sigma * (np.random.default_rng(42).normal(size=len(rotated)) +
                                     1j * np.random.default_rng(43).normal(size=len(rotated)))
        np.asarray(impaired, dtype=np.complex64).tofile(output_path)
        return "NumPy flowgraph-equivalent fallback (GNU Radio unavailable)"

    data = [complex(value) for value in symbols]
    amplitude = float(np.sqrt(np.mean(np.abs(symbols) ** 2)))
    noise_voltage = amplitude / math.sqrt(10 ** (snr_db / 10.0))
    top = gr.top_block("autosig_synthetic_psk")
    source = blocks.vector_source_c(data, False)
    repeat = blocks.repeat(gr.sizeof_gr_complex, samples_per_symbol)
    oscillator = analog.sig_source_c(sample_rate, analog.GR_COS_WAVE, frequency_offset_hz, 1.0, 0.0)
    multiply = blocks.multiply_cc()
    channel = channels.channel_model(noise_voltage=noise_voltage, frequency_offset=0.0,
                                     epsilon=1.0, taps=[1.0 + 0j], noise_seed=42, block_tags=False)
    sink = blocks.file_sink(gr.sizeof_gr_complex, str(output_path), False)
    top.connect(source, repeat, multiply)
    top.connect(oscillator, (multiply, 1))
    top.connect(multiply, channel, sink)
    top.run()
    return "GNU Radio"
