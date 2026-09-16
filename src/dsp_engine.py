import numpy as np
from scipy import signal


class DSPEngine:
    """
    DSP processing engine for:
    FFT, spectrogram, SNR, baud-rate estimation,
    power and RMS estimation.
    """

    # ---------------------------------------------------------
    # FFT
    # ---------------------------------------------------------

    @staticmethod
    def compute_fft(complex_signal, fs):
        x = np.asarray(complex_signal)

        if len(x) == 0:
            raise ValueError("Signal is empty.")

        if fs <= 0:
            raise ValueError("Sampling frequency must be greater than 0.")

        x = x - np.mean(x)

        n = len(x)

        fft_data = np.fft.fft(x)
        fft_data = np.fft.fftshift(fft_data)

        freqs = np.fft.fftfreq(
            n,
            d=1 / fs
        )

        freqs = np.fft.fftshift(freqs)

        magnitude = np.abs(fft_data)

        psd = 20 * np.log10(
            magnitude + 1e-12
        )

        return freqs, psd

    # ---------------------------------------------------------
    # SPECTROGRAM
    # ---------------------------------------------------------

    @staticmethod
    def compute_spectrogram(
        complex_signal,
        fs,
        nperseg=1024,
        noverlap=512
    ):

        x = np.asarray(complex_signal)

        if len(x) == 0:
            raise ValueError("Signal is empty.")

        if fs <= 0:
            raise ValueError(
                "Sampling frequency must be greater than 0."
            )

        nperseg = min(
            nperseg,
            len(x)
        )

        noverlap = min(
            noverlap,
            nperseg - 1
        )

        f, t, Sxx = signal.spectrogram(
            x,
            fs=fs,
            nperseg=nperseg,
            noverlap=noverlap,
            return_onesided=False,
            scaling="density"
        )

        f = np.fft.fftshift(f)

        Sxx = np.fft.fftshift(
            Sxx,
            axes=0
        )

        Sxx_dB = 10 * np.log10(
            np.abs(Sxx) + 1e-12
        )

        return f, t, Sxx_dB

    # ---------------------------------------------------------
    # SNR
    # ---------------------------------------------------------

    @staticmethod
    def estimate_snr(complex_signal):

        x = np.asarray(complex_signal)

        if len(x) == 0:
            raise ValueError("Signal is empty.")

        power = np.abs(x) ** 2

        signal_power = np.percentile(
            power,
            90
        )

        noise_power = np.percentile(
            power,
            10
        )

        if noise_power <= 0:
            return float("inf")

        snr_db = 10 * np.log10(
            signal_power / noise_power
        )

        return float(snr_db)

    # ---------------------------------------------------------
    # IMPROVED BAUD RATE ESTIMATION
    # ---------------------------------------------------------

    @staticmethod
    def estimate_baud_rate(
        complex_signal,
        fs
    ):
        """
        Estimate symbol rate using the transition point
        in signal self-difference.

        For rectangular digital symbols, samples within
        the same symbol are highly similar. Once the lag
        reaches approximately one symbol period, the
        difference rapidly stops increasing.

        This works much better than using the FFT of
        signal magnitude for constant-envelope PSK signals.
        """

        x = np.asarray(
            complex_signal,
            dtype=np.complex128
        )

        if len(x) < 100:
            raise ValueError(
                "Signal is too short for baud estimation."
            )

        if fs <= 0:
            raise ValueError(
                "Sampling frequency must be greater than 0."
            )

        # Limit analysis length for speed
        x = x[
            :min(len(x), 100000)
        ]

        # Remove DC
        x = x - np.mean(x)

        # Maximum lag to investigate
        max_lag = min(
            200,
            len(x) // 10
        )

        if max_lag < 5:
            return 0.0

        difference_power = []

        for lag in range(
            1,
            max_lag + 1
        ):

            diff = (
                x[lag:]
                - x[:-lag]
            )

            power = np.mean(
                np.abs(diff) ** 2
            )

            difference_power.append(
                power
            )

        difference_power = np.asarray(
            difference_power
        )

        # Difference curve slope
        slope = np.diff(
            difference_power
        )

        if len(slope) < 5:
            return 0.0

        # Estimate normal slope before
        # reaching one symbol period
        baseline_count = min(
            5,
            len(slope)
        )

        baseline = np.median(
            slope[:baseline_count]
        )

        # If baseline is too small,
        # use another fallback.
        if baseline <= 1e-8:

            max_power = np.max(
                difference_power
            )

            threshold = (
                0.90 * max_power
            )

            candidates = np.where(
                difference_power >= threshold
            )[0]

            if len(candidates) == 0:
                return 0.0

            lag = int(
                candidates[0] + 1
            )

            return float(
                fs / lag
            )

        # Find point where the slope suddenly
        # drops compared to the initial slope.
        threshold = (
            baseline * 0.25
        )

        candidate_lag = None

        for i in range(
            3,
            len(slope)
        ):

            if slope[i] < threshold:

                candidate_lag = i + 1
                break

        if candidate_lag is None:

            # Fallback using 95% saturation
            threshold_power = (
                0.95
                * np.max(difference_power)
            )

            candidates = np.where(
                difference_power
                >= threshold_power
            )[0]

            if len(candidates) > 0:
                candidate_lag = (
                    int(candidates[0]) + 1
                )

        if candidate_lag is None:
            return 0.0

        # Sanity check
        if candidate_lag <= 0:
            return 0.0

        baud_rate = (
            fs / candidate_lag
        )

        return float(
            baud_rate
        )

    # ---------------------------------------------------------
    # POWER
    # ---------------------------------------------------------

    @staticmethod
    def estimate_power(complex_signal):

        x = np.asarray(
            complex_signal
        )

        if len(x) == 0:
            raise ValueError(
                "Signal is empty."
            )

        return float(
            np.mean(
                np.abs(x) ** 2
            )
        )

    # ---------------------------------------------------------
    # RMS
    # ---------------------------------------------------------

    @staticmethod
    def estimate_rms(complex_signal):

        x = np.asarray(
            complex_signal
        )

        if len(x) == 0:
            raise ValueError(
                "Signal is empty."
            )

        return float(
            np.sqrt(
                np.mean(
                    np.abs(x) ** 2
                )
            )
        )