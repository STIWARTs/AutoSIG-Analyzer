"""Persistent history of AutoSIG analyses backed by SQLite (stdlib only).

The database lives at ``data/autosig.db`` under the project root and is created
on first use. Every completed analysis is written as one row; the queryable
scalar/JSON columns follow the agreed schema, and a ``result_json`` blob holds
the complete serialized :class:`~backend.types.PipelineResult` so that loading a
past run reconstructs the exact in-memory shape the live pipeline produces —
letting the Analysis/Recovery/Bitstream/Report pages render history unchanged.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.types import (AnalysisResult, Hypothesis, IngestedSignal, PipelineResult,
                           RecoveryAttempt, ValidationResult)

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "autosig.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    input_filename TEXT,
    source_format TEXT,
    sample_rate_hz REAL,
    occupied_bandwidth_hz REAL,
    center_frequency_hz REAL,
    estimated_snr_db REAL,
    estimated_symbol_rate_baud REAL,
    classifier_probabilities TEXT,
    hypotheses TEXT,
    accepted_hypothesis TEXT,
    correlation_score REAL,
    header_bits TEXT,
    payload_bits TEXT,
    synchronized_symbols TEXT,
    result_json TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


# --------------------------------------------------------------------------- #
# numpy <-> JSON helpers (complex arrays stored as [real, imag] pairs)
# --------------------------------------------------------------------------- #
def _complex_to_list(values: np.ndarray | None) -> list | None:
    if values is None:
        return None
    arr = np.asarray(values)
    if arr.size == 0:
        return []
    return [[float(z.real), float(z.imag)] for z in arr.astype(np.complex128).ravel()]


def _list_to_complex(payload: list | None) -> np.ndarray | None:
    if payload is None:
        return None
    if len(payload) == 0:
        return np.array([], dtype=np.complex64)
    pairs = np.asarray(payload, dtype=np.float64)
    return (pairs[:, 0] + 1j * pairs[:, 1]).astype(np.complex64)


def _array_to_list(values: np.ndarray | None) -> list | None:
    if values is None:
        return None
    return np.asarray(values).tolist()


def _bits_to_list(values: np.ndarray | None) -> list | None:
    if values is None:
        return None
    return [int(v) for v in np.asarray(values).ravel()]


def _nullable_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if np.isnan(result) else result


# --------------------------------------------------------------------------- #
# Serialization of the full PipelineResult
# --------------------------------------------------------------------------- #
def _hypothesis_to_dict(hypothesis: Hypothesis) -> dict:
    return {"rank": hypothesis.rank, "modulation": hypothesis.modulation,
            "interleaving": hypothesis.interleaving, "fec": hypothesis.fec, "score": hypothesis.score}


def _dict_to_hypothesis(payload: dict) -> Hypothesis:
    return Hypothesis(rank=int(payload["rank"]), modulation=payload["modulation"],
                      interleaving=payload["interleaving"], fec=payload["fec"], score=float(payload["score"]))


def _serialize(result: PipelineResult) -> str:
    analysis = result.analysis
    signal = analysis.signal
    validation = result.validation
    attempts = [{
        "hypothesis": _hypothesis_to_dict(attempt.hypothesis),
        "steps": [[name, status, detail] for name, status, detail in attempt.steps],
        "recovered_bits": _bits_to_list(attempt.recovered_bits),
        "error": attempt.error,
        "synchronized_symbols": _complex_to_list(attempt.synchronized_symbols),
    } for attempt in result.attempts]
    payload = {
        "analysis": {
            "signal": {
                "samples": _complex_to_list(signal.samples),
                "sample_rate": signal.sample_rate,
                "center_frequency": signal.center_frequency,
                "source_format": signal.source_format,
                "filename": signal.filename,
                "metadata": signal.metadata,
            },
            "frequency_hz": _array_to_list(analysis.frequency_hz),
            "psd_db": _array_to_list(analysis.psd_db),
            "spectrogram_frequency_hz": _array_to_list(analysis.spectrogram_frequency_hz),
            "spectrogram_time_s": _array_to_list(analysis.spectrogram_time_s),
            "spectrogram_db": _array_to_list(analysis.spectrogram_db),
            "parameters": dict(analysis.parameters),
        },
        "probabilities": dict(result.probabilities),
        "hypotheses": [_hypothesis_to_dict(hypothesis) for hypothesis in result.hypotheses],
        "attempts": attempts,
        "validation": None if validation is None else {
            "passed": bool(validation.passed),
            "correlation_score": validation.correlation_score,
            "peak_index": validation.peak_index,
            "header_bits": _bits_to_list(validation.header_bits),
            "payload_bits": _bits_to_list(validation.payload_bits),
        },
        "accepted_rank": result.accepted.hypothesis.rank if result.accepted else None,
    }
    return json.dumps(payload, default=str)


def _deserialize(blob: str) -> PipelineResult:
    payload = json.loads(blob)
    analysis_payload = payload["analysis"]
    signal_payload = analysis_payload["signal"]
    signal = IngestedSignal(samples=_list_to_complex(signal_payload["samples"]),
                            sample_rate=signal_payload["sample_rate"],
                            center_frequency=signal_payload["center_frequency"],
                            source_format=signal_payload["source_format"],
                            filename=signal_payload["filename"],
                            metadata=signal_payload.get("metadata", {}))
    analysis = AnalysisResult(
        signal=signal,
        frequency_hz=np.asarray(analysis_payload["frequency_hz"], dtype=np.float64),
        psd_db=np.asarray(analysis_payload["psd_db"], dtype=np.float64),
        spectrogram_frequency_hz=np.asarray(analysis_payload["spectrogram_frequency_hz"], dtype=np.float64),
        spectrogram_time_s=np.asarray(analysis_payload["spectrogram_time_s"], dtype=np.float64),
        spectrogram_db=np.asarray(analysis_payload["spectrogram_db"], dtype=np.float64),
        parameters=dict(analysis_payload["parameters"]),
    )
    attempts: list[RecoveryAttempt] = []
    for attempt_payload in payload["attempts"]:
        attempts.append(RecoveryAttempt(
            hypothesis=_dict_to_hypothesis(attempt_payload["hypothesis"]),
            steps=[(name, status, detail) for name, status, detail in attempt_payload["steps"]],
            recovered_bits=None if attempt_payload["recovered_bits"] is None
            else np.asarray(attempt_payload["recovered_bits"], dtype=np.uint8),
            error=attempt_payload["error"],
            synchronized_symbols=_list_to_complex(attempt_payload["synchronized_symbols"]),
        ))
    by_rank = {attempt.hypothesis.rank: attempt for attempt in attempts}
    accepted = by_rank.get(payload["accepted_rank"]) if payload.get("accepted_rank") is not None else None
    validation_payload = payload["validation"]
    validation = None if validation_payload is None else ValidationResult(
        passed=bool(validation_payload["passed"]),
        correlation_score=float(validation_payload["correlation_score"]),
        peak_index=int(validation_payload["peak_index"]),
        header_bits=np.asarray(validation_payload["header_bits"], dtype=np.uint8),
        payload_bits=np.asarray(validation_payload["payload_bits"], dtype=np.uint8),
    )
    return PipelineResult(analysis, payload["probabilities"],
                          [_dict_to_hypothesis(h) for h in payload["hypotheses"]], attempts, validation, accepted)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def save_analysis(result: PipelineResult) -> int:
    """Persist one completed analysis (validated or not) and return its row id."""
    params = result.analysis.parameters
    accepted = result.accepted
    validation = result.validation
    hypotheses = [_hypothesis_to_dict(hypothesis) for hypothesis in result.hypotheses]
    accepted_dict = _hypothesis_to_dict(accepted.hypothesis) if accepted else None
    symbols = _complex_to_list(accepted.synchronized_symbols) if accepted else None
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO analyses (
                   timestamp, input_filename, source_format, sample_rate_hz, occupied_bandwidth_hz,
                   center_frequency_hz, estimated_snr_db, estimated_symbol_rate_baud,
                   classifier_probabilities, hypotheses, accepted_hypothesis, correlation_score,
                   header_bits, payload_bits, synchronized_symbols, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                result.analysis.signal.filename,
                result.analysis.signal.source_format,
                _nullable_float(params.get("sample_rate_hz")),
                _nullable_float(params.get("occupied_bandwidth_hz")),
                _nullable_float(params.get("center_frequency_hz")),
                _nullable_float(params.get("estimated_snr_db")),
                _nullable_float(params.get("estimated_symbol_rate_baud")),
                json.dumps(result.probabilities, default=str),
                json.dumps(hypotheses, default=str),
                json.dumps(accepted_dict, default=str) if accepted_dict else None,
                _nullable_float(validation.correlation_score) if validation else None,
                "".join(map(str, validation.header_bits)) if validation else None,
                "".join(map(str, validation.payload_bits)) if validation else None,
                json.dumps(symbols) if symbols else None,
                _serialize(result),
            ),
        )
        return int(cursor.lastrowid)


def list_recent(limit: int = 10) -> list[dict[str, Any]]:
    """Return the most recent analyses as compact summaries for the Dashboard."""
    with _connect() as conn:
        rows = conn.execute(
            """SELECT id, timestamp, input_filename, accepted_hypothesis, correlation_score
               FROM analyses ORDER BY id DESC LIMIT ?""",
            (int(limit),),
        ).fetchall()
    summaries = []
    for row in rows:
        accepted = json.loads(row["accepted_hypothesis"]) if row["accepted_hypothesis"] else None
        summaries.append({
            "id": int(row["id"]),
            "timestamp": row["timestamp"],
            "input_filename": row["input_filename"],
            "accepted_modulation": accepted["modulation"] if accepted else None,
            "correlation_score": row["correlation_score"],
        })
    return summaries


def load_analysis(analysis_id: int) -> PipelineResult:
    """Reconstruct the full in-memory PipelineResult for a stored analysis id."""
    with _connect() as conn:
        row = conn.execute("SELECT result_json FROM analyses WHERE id = ?", (int(analysis_id),)).fetchone()
    if row is None:
        raise KeyError(f"No stored analysis with id {analysis_id}")
    return _deserialize(row["result_json"])
