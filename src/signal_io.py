import numpy as np
from scipy.io import wavfile
import os

class SignalLoader:
    """Handles reading, normalization, and IQ format detection for .iq and .wav files."""
    
    @staticmethod
    def load_file(file_path, iq_format='complex64', sample_rate=1e6):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.wav':
            return SignalLoader._load_wav(file_path)
        elif ext == '.iq' or ext == '.dat':
            return SignalLoader._load_iq(file_path, iq_format), sample_rate
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _load_wav(file_path):
        fs, data = wavfile.read(file_path)
        if data.ndim == 2:  # Stereo file treated as I/Q channels
            i_chan = data[:, 0].astype(np.float32)
            q_chan = data[:, 1].astype(np.float32)
            complex_signal = i_chan + 1j * q_chan
        else:  # Mono file converted to analytic signal via Hilbert transform
            from scipy.signal import hilbert
            complex_signal = hilbert(data.astype(np.float32))
        
        # Normalize signal amplitude
        max_val = np.max(np.abs(complex_signal))
        if max_val > 0:
            complex_signal = complex_signal / max_val
        return complex_signal, fs

    @staticmethod
    def _load_iq(file_path, iq_format='complex64'):
        dtype_map = {
            'complex64': np.complex64,
            'complex128': np.complex128,
            'int16': np.int16,
            'float32': np.float32
        }
        dtype = dtype_map.get(iq_format, np.complex64)
        
        with open(file_path, 'rb') as f:
            raw_data = np.fromfile(f, dtype=dtype)
            
        if dtype in [np.int16, np.float32]:
            # Interleaved I/Q (I, Q, I, Q, ...)
            if len(raw_data) % 2 != 0:
                raw_data = raw_data[:-1]
            i_chan = raw_data[0::2].astype(np.float32)
            q_chan = raw_data[1::2].astype(np.float32)
            complex_signal = i_chan + 1j * q_chan
        else:
            complex_signal = raw_data.astype(np.complex64)

        max_val = np.max(np.abs(complex_signal))
        if max_val > 0:
            complex_signal /= max_val
        return complex_signal