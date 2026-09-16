import numpy as np


class ModulationAnalyzer:
    """
    Automatic modulation classification and demodulation.

    Supported:
        BPSK
        QPSK
        8PSK
        16QAM
        FSK
    """

    MOD_TYPES = [
        "BPSK",
        "QPSK",
        "8PSK",
        "16QAM",
        "FSK"
    ]

    # ---------------------------------------------------------
    # MODULATION CLASSIFICATION
    # ---------------------------------------------------------

    @staticmethod
    def classify_modulation(
        complex_signal,
        fs=1e6,
        baud_rate=None
    ):

        x = np.asarray(
            complex_signal,
            dtype=np.complex128
        )

        if len(x) < 100:
            raise ValueError(
                "Signal is too short for classification."
            )

        # Remove DC
        x = x - np.mean(x)

        # Normalize
        amplitude = np.abs(x)

        mean_amplitude = np.mean(
            amplitude
        )

        if mean_amplitude <= 1e-12:
            raise ValueError(
                "Signal amplitude is zero."
            )

        x_norm = (
            x / mean_amplitude
        )

        amplitude_norm = np.abs(
            x_norm
        )

        # -----------------------------------------------------
        # 1. Detect FSK
        # -----------------------------------------------------

        phase = np.unwrap(
            np.angle(x_norm)
        )

        instantaneous_frequency = np.diff(
            phase
        )

        instantaneous_frequency = (
            instantaneous_frequency[
                np.isfinite(
                    instantaneous_frequency
                )
            ]
        )

        if len(
            instantaneous_frequency
        ) > 20:

            abs_freq = np.abs(
                instantaneous_frequency
            )

            median_freq = np.median(
                abs_freq
            )

            p90_freq = np.percentile(
                abs_freq,
                90
            )

            # FSK has continuous frequency deviation.
            #
            # PSK generally has near-zero frequency
            # except around symbol transitions.

            if (
                median_freq > 0.10
                and
                p90_freq < median_freq * 3.0
            ):
                return "FSK"

        # -----------------------------------------------------
        # 2. Check amplitude variation
        # -----------------------------------------------------

        amplitude_variance = np.var(
            amplitude_norm
        )

        # 16QAM has multiple amplitude levels.
        if amplitude_variance > 0.12:

            return "16QAM"

        # -----------------------------------------------------
        # 3. PSK classification
        # -----------------------------------------------------

        phase_values = np.mod(
            np.angle(x_norm),
            2 * np.pi
        )

        # Ignore very low amplitude samples
        valid = (
            amplitude_norm
            > 0.3
        )

        phase_values = phase_values[
            valid
        ]

        if len(phase_values) == 0:
            return "BPSK"

        # -----------------------------------------------------
        # Test BPSK
        # -----------------------------------------------------

        bpsk_error = (
            ModulationAnalyzer
            ._phase_quantization_error(
                phase_values,
                2
            )
        )

        # -----------------------------------------------------
        # Test QPSK
        # -----------------------------------------------------

        qpsk_error = (
            ModulationAnalyzer
            ._phase_quantization_error(
                phase_values,
                4
            )
        )

        # -----------------------------------------------------
        # Test 8PSK
        # -----------------------------------------------------

        psk8_error = (
            ModulationAnalyzer
            ._phase_quantization_error(
                phase_values,
                8
            )
        )

        # BPSK
        if bpsk_error < 0.20:

            return "BPSK"

        # QPSK
        if qpsk_error < 0.20:

            return "QPSK"

        # 8PSK
        if psk8_error < 0.20:

            return "8PSK"

        # Fallback
        return "BPSK"

    # ---------------------------------------------------------
    # PHASE QUANTIZATION ERROR
    # ---------------------------------------------------------

    @staticmethod
    def _phase_quantization_error(
        phase_values,
        m
    ):
        """
        Measure how closely phase samples match
        an M-PSK constellation.

        The constellation rotation is unknown,
        so all possible phase offsets are tested.
        """

        phase_values = np.asarray(
            phase_values
        )

        step = (
            2 * np.pi / m
        )

        # Estimate best constellation rotation
        #
        # Test several offsets.
        offsets = np.linspace(
            0,
            step,
            64,
            endpoint=False
        )

        best_error = np.inf

        for offset in offsets:

            normalized_phase = (
                phase_values
                - offset
            )

            nearest = (
                np.round(
                    normalized_phase
                    / step
                )
                * step
            )

            error = (
                normalized_phase
                - nearest
            )

            # Wrap to [-pi, pi]
            error = (
                np.angle(
                    np.exp(
                        1j * error
                    )
                )
            )

            mean_error = np.mean(
                np.abs(error)
            )

            if mean_error < best_error:
                best_error = mean_error

        return float(
            best_error
        )

    # ---------------------------------------------------------
    # DEMODULATION
    # ---------------------------------------------------------

    @staticmethod
    def demodulate(
        complex_signal,
        mod_type,
        fs,
        baud_rate
    ):

        x = np.asarray(
            complex_signal,
            dtype=np.complex128
        )

        if len(x) == 0:
            raise ValueError(
                "Signal is empty."
            )

        if fs <= 0:
            raise ValueError(
                "Sampling frequency must be greater than zero."
            )

        if baud_rate <= 0:
            raise ValueError(
                "Baud rate must be greater than zero."
            )

        if mod_type not in (
            ModulationAnalyzer.MOD_TYPES
        ):
            raise NotImplementedError(
                f"Unsupported modulation: {mod_type}"
            )

        # Samples per symbol
        sps = max(
            int(
                round(
                    fs / baud_rate
                )
            ),
            1
        )

        # -----------------------------------------------------
        # Matched/simple rectangular filter
        # -----------------------------------------------------

        if sps > 1:

            pulse = (
                np.ones(sps)
                / sps
            )

            filtered = np.convolve(
                x,
                pulse,
                mode="same"
            )

        else:

            filtered = x

        # Sample near symbol centers
        start = max(
            sps // 2,
            0
        )

        sampled = filtered[
            start::sps
        ]

        # -----------------------------------------------------
        # BPSK
        # -----------------------------------------------------

        if mod_type == "BPSK":

            bits = (
                np.real(sampled)
                >= 0
            ).astype(
                np.uint8
            )

            return bits, sampled

        # -----------------------------------------------------
        # QPSK
        # -----------------------------------------------------

        elif mod_type == "QPSK":

            i_bits = (
                np.real(sampled)
                >= 0
            ).astype(
                np.uint8
            )

            q_bits = (
                np.imag(sampled)
                >= 0
            ).astype(
                np.uint8
            )

            bits = np.column_stack(
                (
                    i_bits,
                    q_bits
                )
            ).ravel()

            return bits, sampled

        # -----------------------------------------------------
        # 8PSK
        # -----------------------------------------------------

        elif mod_type == "8PSK":

            phase = np.mod(
                np.angle(sampled),
                2 * np.pi
            )

            symbol_index = np.floor(
                (
                    phase
                    + np.pi / 8
                )
                /
                (
                    2 * np.pi / 8
                )
            ).astype(
                np.uint8
            )

            symbol_index %= 8

            bits = []

            for symbol in symbol_index:

                bits.extend(
                    [
                        (symbol >> 2) & 1,
                        (symbol >> 1) & 1,
                        symbol & 1
                    ]
                )

            return (
                np.array(
                    bits,
                    dtype=np.uint8
                ),
                sampled
            )

        # -----------------------------------------------------
        # 16QAM
        # -----------------------------------------------------

        elif mod_type == "16QAM":

            real_part = np.real(
                sampled
            )

            imag_part = np.imag(
                sampled
            )

            scale = np.max(
                np.abs(
                    np.concatenate(
                        (
                            real_part,
                            imag_part
                        )
                    )
                )
            )

            if scale > 0:

                real_part /= scale
                imag_part /= scale

            def quantize(value):

                if value < -0.5:
                    return 0

                elif value < 0:
                    return 1

                elif value < 0.5:
                    return 2

                else:
                    return 3

            i_symbols = np.array(
                [
                    quantize(v)
                    for v in real_part
                ],
                dtype=np.uint8
            )

            q_symbols = np.array(
                [
                    quantize(v)
                    for v in imag_part
                ],
                dtype=np.uint8
            )

            bits = []

            for i_sym, q_sym in zip(
                i_symbols,
                q_symbols
            ):

                bits.extend(
                    [
                        (i_sym >> 1) & 1,
                        i_sym & 1,
                        (q_sym >> 1) & 1,
                        q_sym & 1
                    ]
                )

            return (
                np.array(
                    bits,
                    dtype=np.uint8
                ),
                sampled
            )

        # -----------------------------------------------------
        # FSK
        # -----------------------------------------------------

        elif mod_type == "FSK":

            phase = np.unwrap(
                np.angle(x)
            )

            instantaneous_frequency = (
                np.diff(phase)
            )

            freq_samples = (
                instantaneous_frequency[
                    start::sps
                ]
            )

            if len(
                freq_samples
            ) == 0:

                return (
                    np.array(
                        [],
                        dtype=np.uint8
                    ),
                    freq_samples
                )

            threshold = np.median(
                freq_samples
            )

            bits = (
                freq_samples
                >= threshold
            ).astype(
                np.uint8
            )

            return (
                bits,
                freq_samples
            )

        raise NotImplementedError(
            f"Demodulation not implemented "
            f"for {mod_type}"
        )