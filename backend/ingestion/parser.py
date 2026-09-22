from __future__ import annotations

import io
import json
from pathlib import Path
from typing import BinaryIO

import numpy as np
from scipy.io import wavfile

from backend.types import IngestedSignal


def _sigmf_fields(metadata: dict) -> tuple[float, float | None, str]:
    global_meta = metadata.get("global", metadata)
    captures = metadata.get("captures", [])
    capture = captures[0] if captures else {}
    sample_rate = global_meta.get("core:sample_rate")
    datatype = global_meta.get("core:datatype", "cf32_le")
    center_frequency = capture.get("core:frequency", global_meta.get("core:frequency"))
    if sample_rate is None:
        raise ValueError("SigMF metadata must include global.core:sample_rate")
    return float(sample_rate), (float(center_frequency) if center_frequency is not None else None), datatype


def _decode_iq(raw: bytes, datatype: str) -> np.ndarray:
    datatype = datatype.lower()
    if datatype.startswith("cf32"):
        values = np.frombuffer(raw, dtype="<f4")
        return (values[0::2] + 1j * values[1::2]).astype(np.complex64)
    if datatype.startswith("ci16"):
        values = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
        return (values[0::2] + 1j * values[1::2]).astype(np.complex64)
    raise ValueError(f"Unsupported SigMF datatype: {datatype}. Supported: cf32_le, ci16_le")


def load_iq(data_path: str | Path | BinaryIO, metadata_path: str | Path | BinaryIO | None = None,
            filename: str = "", sample_rate: float | None = None, datatype: str = "cf32_le",
            center_frequency: float | None = None) -> IngestedSignal:
    def read_bytes(value: str | Path | BinaryIO) -> bytes:
        if hasattr(value, "read"):
            if hasattr(value, "seek"):
                value.seek(0)
            return value.read()
        return Path(value).read_bytes()

    metadata: dict = {}
    if metadata_path is not None:
        metadata = json.loads(read_bytes(metadata_path).decode("utf-8"))
        sample_rate, center_frequency, datatype = _sigmf_fields(metadata)
    elif sample_rate is not None:
        metadata = {"autosig:metadata_source": "manual", "core:datatype": datatype}
    else:
        metadata = {"autosig:metadata_source": "unavailable", "core:datatype": datatype}
    samples = _decode_iq(read_bytes(data_path), datatype)
    return IngestedSignal(samples=samples, sample_rate=sample_rate, center_frequency=center_frequency,
                          source_format="iq", filename=filename, metadata=metadata)


def load_wav(data_path: str | Path | BinaryIO, filename: str = "") -> IngestedSignal:
    if hasattr(data_path, "read"):
        if hasattr(data_path, "seek"):
            data_path.seek(0)
        raw = data_path.read()
        sample_rate, data = wavfile.read(io.BytesIO(raw))
    else:
        sample_rate, data = wavfile.read(str(data_path))
    data = np.asarray(data)
    if np.issubdtype(data.dtype, np.integer):
        data = data.astype(np.float32) / np.iinfo(data.dtype).max
    else:
        data = data.astype(np.float32)
    if data.ndim == 1:
        samples = data.astype(np.complex64)
    elif data.shape[1] >= 2:
        samples = (data[:, 0] + 1j * data[:, 1]).astype(np.complex64)
    else:
        raise ValueError("WAV has no usable channel data")
    return IngestedSignal(samples=samples, sample_rate=float(sample_rate), center_frequency=None,
                          source_format="wav", filename=filename)


def parse_upload(signal_file, sigmf_file=None, sample_rate: float | None = None,
                 datatype: str = "cf32_le", center_frequency: float | None = None) -> IngestedSignal:
    suffix = Path(signal_file.name).suffix.lower()
    if suffix == ".iq":
        return load_iq(signal_file, sigmf_file, signal_file.name, sample_rate, datatype, center_frequency)
    if suffix == ".wav":
        return load_wav(signal_file, signal_file.name)
    raise ValueError("Only .iq and .wav uploads are supported.")
