import os
import numpy as np

from src.signal_io import SignalLoader
from src.dsp_engine import DSPEngine
from src.fec_interleave import FECAndInterleaver
from src.correlation import BitstreamCorrelator


class AnalysisController:
    """Application/service layer between the PyQt GUI and DSP modules.

    Existing signal-processing modules are reused. The controller only
    orchestrates them and converts their output into UI-friendly results.
    """

    MOD_TYPES = ["BPSK", "QPSK", "8PSK", "16QAM", "FSK"]

    def __init__(self):
        self.signal_data = None
        self.fs = 1e6
        self.file_path = None
        self.results = {}

    # ---------------------------------------------------------
    # File ingestion
    # ---------------------------------------------------------
    def load_signal(self, file_path, iq_format="complex64"):
        signal_data, fs = SignalLoader.load_file(
            file_path, iq_format=iq_format
        )
        self.signal_data = np.asarray(signal_data)
        self.fs = float(fs)
        self.file_path = file_path
        self.results = {}
        return self.metadata()

    def metadata(self):
        if self.signal_data is None:
            return {}

        size_bytes = os.path.getsize(self.file_path) if self.file_path else 0
        duration = len(self.signal_data) / self.fs if self.fs else 0
        ext = os.path.splitext(self.file_path or "")[1].lower()

        return {
            "file_name": os.path.basename(self.file_path or ""),
            "file_path": self.file_path or "",
            "file_type": ext.replace(".", "").upper() or "UNKNOWN",
            "file_size": self._format_bytes(size_bytes),
            "file_size_bytes": size_bytes,
            "samples": int(len(self.signal_data)),
            "sampling_rate": self.fs,
            "sampling_rate_text": self._format_rate(self.fs),
            "duration": duration,
            "duration_text": self._format_duration(duration),
            "channel": "Complex IQ" if np.iscomplexobj(self.signal_data) else "Mono",
            "sample_format": str(self.signal_data.dtype),
        }

    # ---------------------------------------------------------
    # Main analysis orchestration
    # ---------------------------------------------------------
    def analyze_signal(self, progress_callback=None):
        if self.signal_data is None:
            raise RuntimeError("Load a signal file first.")

        signal_data = self.signal_data
        total_steps = 9

        def progress(stage, value):
            if progress_callback:
                progress_callback(int(value), stage)

        progress("Signal preprocessing", 8)

        power = DSPEngine.estimate_power(signal_data)
        rms = DSPEngine.estimate_rms(signal_data)
        snr = DSPEngine.estimate_snr(signal_data)

        progress("FFT / spectrum analysis", 20)
        fft_signal = signal_data[: min(len(signal_data), 16384)]
        freqs, psd = DSPEngine.compute_fft(fft_signal, self.fs)

        progress("Waterfall generation", 30)
        spectrogram_signal = signal_data[: min(len(signal_data), 32768)]
        spec_f, spec_t, spec_db = DSPEngine.compute_spectrogram(
            spectrogram_signal, self.fs
        )

        progress("Symbol-rate estimation", 42)
        raw_baud = DSPEngine.estimate_baud_rate(signal_data, self.fs)
        baud = self.refine_baud_rate(raw_baud)

        progress("Feature extraction", 52)
        symbols = self.extract_symbols(signal_data, baud)

        progress("Modulation hypothesis generation", 64)
        candidates = self.modulation_candidates(symbols, signal_data)
        detected_mod = candidates[0]["name"] if candidates else "Unknown"

        progress("Demodulation", 76)
        bits = self.demodulate_symbols(symbols, detected_mod)

        progress("Validation / decoding", 88)
        filename = os.path.basename(self.file_path or "").lower()
        synthetic = filename.startswith("sample_")

        decoded_bits = bits
        preamble_name = None
        preamble_index = -1
        preamble_confidence = 0.0
        payload = np.array([], dtype=np.uint8)
        fec_status = "Skipped — synthetic raw-symbol test"
        interleaving_status = "Skipped — synthetic raw-symbol test"
        validation_status = "Synthetic test stream"

        if not synthetic:
            if len(bits) >= 128:
                decoded_bits = FECAndInterleaver.deinterleave_block(
                    bits, rows=8, cols=16
                )
                interleaving_status = "Block 8 × 16 applied"

            if len(decoded_bits) >= 2:
                decoded_bits = FECAndInterleaver.viterbi_decode_hard(
                    decoded_bits
                )
                fec_status = "Viterbi hard-decision applied"

            preamble_name, preamble_index, preamble_confidence = (
                BitstreamCorrelator.detect_preamble(decoded_bits)
            )

            if preamble_index >= 0 and preamble_confidence >= 0.80:
                payload = BitstreamCorrelator.extract_payload(
                    decoded_bits,
                    preamble_index,
                    len(BitstreamCorrelator.PREAMBLES[preamble_name]),
                    payload_len=64,
                )
                validation_status = "Preamble validated"
            else:
                validation_status = "No reliable preamble validation"

        progress("Finalizing results", 100)

        peak_freq, peak_power = self._peak_measurement(freqs, psd)
        bandwidth = self._estimate_bandwidth(freqs, psd, peak_power)
        confidence = self._overall_confidence(candidates, preamble_confidence, synthetic)

        self.results = {
            "power": float(power),
            "rms": float(rms),
            "snr": float(snr),
            "raw_baud": float(raw_baud),
            "baud": float(baud),
            "symbols": symbols,
            "bits": bits,
            "decoded_bits": decoded_bits,
            "freqs": freqs,
            "psd": psd,
            "spec_f": spec_f,
            "spec_t": spec_t,
            "spec_db": spec_db,
            "candidates": candidates,
            "modulation": detected_mod,
            "peak_frequency": float(peak_freq),
            "peak_power": float(peak_power),
            "bandwidth": float(bandwidth),
            "center_frequency": float(peak_freq),
            "frequency_offset": float(peak_freq),
            "carrier_offset": float(peak_freq),
            "evm": self._estimate_evm(symbols, detected_mod),
            "ber": None,
            "preamble_name": preamble_name,
            "preamble_index": int(preamble_index),
            "preamble_confidence": float(preamble_confidence),
            "payload": payload,
            "fec": fec_status,
            "interleaving": interleaving_status,
            "validation": validation_status,
            "confidence": confidence,
            "synthetic": synthetic,
        }
        return self.results

    # ---------------------------------------------------------
    # Existing pipeline helpers moved out of the GUI
    # ---------------------------------------------------------
    def refine_baud_rate(self, estimated_baud):
        if estimated_baud <= 0:
            return estimated_baud
        raw_sps = self.fs / estimated_baud
        center = int(round(raw_sps))
        candidates = []
        for sps in range(max(1, center - 3), center + 4):
            baud = self.fs / sps
            candidates.append((abs(baud - estimated_baud), baud))
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def extract_symbols(self, signal_data, baud_rate):
        if baud_rate <= 0:
            return np.array([], dtype=np.complex128)
        sps = int(round(self.fs / baud_rate))
        if sps <= 0:
            return np.array([], dtype=np.complex128)
        kernel = np.ones(sps) / np.sqrt(sps)
        filtered = np.convolve(signal_data, kernel, mode="same")
        return filtered[sps // 2 :: sps]

    def modulation_candidates(self, symbols, signal_data):
        x = np.asarray(symbols, dtype=np.complex128)
        if len(x) < 20:
            return [{"name": "BPSK", "confidence": 1.0, "score": 0.0}]

        x = x - np.mean(x)
        scale = np.sqrt(np.mean(np.abs(x) ** 2))
        if scale <= 1e-12:
            return [{"name": "BPSK", "confidence": 1.0, "score": 0.0}]
        x = x / scale
        test = x[: min(len(x), 5000)]
        amplitude = np.abs(x)

        references = {
            "BPSK": np.array([-1 + 0j, 1 + 0j]),
            "QPSK": np.array([1+1j, 1-1j, -1+1j, -1-1j]) / np.sqrt(2),
            "8PSK": np.exp(1j * np.arange(8) * 2 * np.pi / 8),
            "16QAM": self._qam16_reference(),
        }
        scores = {}
        for name, ref in references.items():
            distances = np.min(np.abs(test[:, None] - ref[None, :]) ** 2, axis=1)
            scores[name] = float(np.mean(distances))

        phase = np.unwrap(np.angle(signal_data))
        inst_freq = np.diff(phase)
        if len(inst_freq) > 100:
            hist, _ = np.histogram(inst_freq, bins=80)
            peaks = int(np.sum(hist > 0.25 * np.max(hist))) if np.max(hist) > 0 else 0
            if peaks >= 2 and np.var(amplitude) < 0.08 and np.std(inst_freq) > 0.02:
                scores["FSK"] = float(max(scores.values()) * 0.55)
            else:
                scores["FSK"] = float(max(scores.values()) * 1.35)
        else:
            scores["FSK"] = float(max(scores.values()) * 1.35)

        bpsk_q_ratio = np.std(np.imag(test)) / (np.std(np.real(test)) + 1e-12)
        if bpsk_q_ratio < 0.25 and scores["BPSK"] < scores["QPSK"] * 1.5:
            scores["BPSK"] *= 0.60

        ordered = sorted(scores.items(), key=lambda item: item[1])
        # Convert inverse distance into relative candidate confidence.
        inv = np.array([1.0 / (score + 1e-9) for _, score in ordered])
        probs = inv / np.sum(inv)
        return [
            {"name": name, "confidence": float(prob), "score": float(score)}
            for (name, score), prob in zip(ordered, probs)
        ]

    def demodulate_symbols(self, symbols, modulation):
        x = np.asarray(symbols, dtype=np.complex128)
        if len(x) == 0:
            return np.array([], dtype=np.uint8)
        if modulation == "BPSK":
            return (np.real(x) >= 0).astype(np.uint8)
        if modulation == "QPSK":
            return np.column_stack(((np.real(x) >= 0), (np.imag(x) >= 0))).astype(np.uint8).ravel()
        if modulation == "8PSK":
            phase = np.mod(np.angle(x), 2 * np.pi)
            symbols_idx = np.floor((phase + np.pi / 8) / (2 * np.pi / 8)).astype(np.uint8) % 8
            bits = []
            for symbol in symbols_idx:
                bits.extend([(symbol >> 2) & 1, (symbol >> 1) & 1, symbol & 1])
            return np.asarray(bits, dtype=np.uint8)
        if modulation == "16QAM":
            real = np.real(x)
            imag = np.imag(x)
            scale = np.max(np.abs(np.concatenate((real, imag))))
            if scale > 0:
                real /= scale
                imag /= scale
            def quantize(v):
                if v < -0.5: return 0
                if v < 0: return 1
                if v < 0.5: return 2
                return 3
            bits = []
            for i, q in zip(map(quantize, real), map(quantize, imag)):
                bits.extend([(i >> 1) & 1, i & 1, (q >> 1) & 1, q & 1])
            return np.asarray(bits, dtype=np.uint8)
        if modulation == "FSK":
            phase = np.unwrap(np.angle(x))
            freq = np.diff(phase)
            if len(freq) == 0:
                return np.array([], dtype=np.uint8)
            return (freq >= np.median(freq)).astype(np.uint8)
        return np.array([], dtype=np.uint8)

    # ---------------------------------------------------------
    # Measurement helpers
    # ---------------------------------------------------------
    def _peak_measurement(self, freqs, psd):
        if len(freqs) == 0:
            return 0.0, 0.0
        idx = int(np.argmax(psd))
        return float(freqs[idx]), float(psd[idx])

    def _estimate_bandwidth(self, freqs, psd, peak_power):
        if len(freqs) < 3:
            return 0.0
        threshold = peak_power - 3.0
        mask = psd >= threshold
        if not np.any(mask):
            return 0.0
        return float(abs(freqs[np.where(mask)[0][-1]] - freqs[np.where(mask)[0][0]]))

    def _estimate_evm(self, symbols, modulation):
        if len(symbols) < 10 or modulation not in ("BPSK", "QPSK", "8PSK", "16QAM"):
            return None
        x = np.asarray(symbols, dtype=np.complex128)
        rms = np.sqrt(np.mean(np.abs(x) ** 2))
        if rms <= 1e-12:
            return None
        x = x / rms
        if modulation == "BPSK":
            ref = np.sign(np.real(x)) + 0j
        elif modulation == "QPSK":
            ref = np.sign(np.real(x)) + 1j * np.sign(np.imag(x))
            ref /= np.sqrt(2)
        elif modulation == "8PSK":
            phase = np.mod(np.angle(x), 2 * np.pi)
            idx = np.floor((phase + np.pi/8) / (2*np.pi/8)).astype(int) % 8
            ref = np.exp(1j * idx * 2 * np.pi / 8)
        else:
            levels = np.array([-3, -1, 1, 3])
            xr = np.real(x)
            xi = np.imag(x)
            ref_r = levels[np.argmin(np.abs(xr[:, None] - levels[None, :]), axis=1)]
            ref_i = levels[np.argmin(np.abs(xi[:, None] - levels[None, :]), axis=1)]
            ref = ref_r + 1j * ref_i
            ref /= np.sqrt(np.mean(np.abs(ref) ** 2))
        return float(100 * np.sqrt(np.mean(np.abs(x - ref) ** 2)))

    def _overall_confidence(self, candidates, preamble_confidence, synthetic):
        if not candidates:
            return 0.0
        modulation_conf = candidates[0]["confidence"]
        if synthetic:
            return float(modulation_conf)
        return float(0.65 * modulation_conf + 0.35 * preamble_confidence)

    @staticmethod
    def _qam16_reference():
        levels = np.array([-3, -1, 1, 3])
        ref = np.array([i + 1j*q for i in levels for q in levels])
        return ref / np.sqrt(np.mean(np.abs(ref) ** 2))

    @staticmethod
    def _format_bytes(value):
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(value)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}"
            value /= 1024

    @staticmethod
    def _format_rate(value):
        value = float(value)
        if value >= 1e9: return f"{value/1e9:.3f} GSPS"
        if value >= 1e6: return f"{value/1e6:.3f} MSPS"
        if value >= 1e3: return f"{value/1e3:.3f} KSPS"
        return f"{value:.1f} SPS"

    @staticmethod
    def _format_duration(seconds):
        seconds = max(0, int(seconds))
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

