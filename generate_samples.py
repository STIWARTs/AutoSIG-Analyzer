import os
import numpy as np
from scipy.io import wavfile


def generate_test_data():
    os.makedirs("data", exist_ok=True)

    # -----------------------------
    # Common Parameters
    # -----------------------------
    fs = 1_000_000          # 1 MHz
    num_samples = 100_000
    baud = 50_000           # 50 kBaud
    sps = int(fs / baud)    # 20 samples/symbol

    rng = np.random.default_rng(42)

    # 5000 symbols are required for 100000 samples
    num_symbols = num_samples // sps

    # =========================================================
    # 1. BPSK IQ
    # =========================================================
    bits_bpsk = rng.integers(0, 2, num_symbols)

    symbols_bpsk = 2 * bits_bpsk - 1

    iq_bpsk = np.repeat(
        symbols_bpsk,
        sps
    ).astype(np.complex64)

    noise = 0.05 * (
        rng.standard_normal(num_samples)
        + 1j * rng.standard_normal(num_samples)
    )

    iq_bpsk += noise.astype(np.complex64)

    iq_bpsk.tofile("data/sample_bpsk.iq")

    print("[+] Generated data/sample_bpsk.iq")


    # =========================================================
    # 2. QPSK WAV
    # =========================================================
    bits_i = rng.integers(0, 2, num_symbols)
    bits_q = rng.integers(0, 2, num_symbols)

    i_symbols = 2 * bits_i - 1
    q_symbols = 2 * bits_q - 1

    iq_qpsk = (
        i_symbols + 1j * q_symbols
    )

    iq_qpsk = np.repeat(
        iq_qpsk,
        sps
    ).astype(np.complex64)

    noise = 0.05 * (
        rng.standard_normal(num_samples)
        + 1j * rng.standard_normal(num_samples)
    )

    iq_qpsk += noise.astype(np.complex64)

    # Normalize separately for WAV conversion
    max_i = np.max(np.abs(np.real(iq_qpsk)))
    max_q = np.max(np.abs(np.imag(iq_qpsk)))

    wav_i = (
        np.real(iq_qpsk) / max_i * 32767
    ).astype(np.int16)

    wav_q = (
        np.imag(iq_qpsk) / max_q * 32767
    ).astype(np.int16)

    wav_stereo = np.column_stack(
        (wav_i, wav_q)
    )

    wavfile.write(
        "data/sample_qpsk.wav",
        fs,
        wav_stereo
    )

    print("[+] Generated data/sample_qpsk.wav")


    # =========================================================
    # 3. FSK IQ
    # =========================================================
    bits_fsk = rng.integers(0, 2, num_symbols)

    # Two frequency levels
    f0 = -25_000
    f1 = 25_000

    frequencies = np.where(
        bits_fsk == 0,
        f0,
        f1
    )

    symbol_frequencies = np.repeat(
        frequencies,
        sps
    )

    # Generate continuous phase
    phase = (
        2 * np.pi
        * np.cumsum(symbol_frequencies)
        / fs
    )

    iq_fsk = np.exp(1j * phase)

    noise = 0.05 * (
        rng.standard_normal(num_samples)
        + 1j * rng.standard_normal(num_samples)
    )

    iq_fsk += noise

    iq_fsk = iq_fsk.astype(np.complex64)

    iq_fsk.tofile(
        "data/sample_fsk.iq"
    )

    print("[+] Generated data/sample_fsk.iq")


    # =========================================================
    # Summary
    # =========================================================
    print()
    print("======================================")
    print(" Test Signal Generation Complete")
    print("======================================")
    print(f"Sampling Rate : {fs / 1e6:.1f} MHz")
    print(f"Baud Rate     : {baud / 1000:.1f} kBaud")
    print(f"Samples       : {num_samples:,}")
    print(f"Samples/Symbol: {sps}")
    print()
    print("Generated files:")
    print("  data/sample_bpsk.iq")
    print("  data/sample_qpsk.wav")
    print("  data/sample_fsk.iq")
    print("======================================")


if __name__ == "__main__":
    generate_test_data()