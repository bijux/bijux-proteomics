# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Streaming import execution over large MGF, mzML, and TSV runtime inputs."""

from __future__ import annotations

from collections.abc import Iterator
import csv
from enum import StrEnum
from pathlib import Path
import tracemalloc

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.io.formats import stream_mzml_spectra
from bijux_proteomics.io.spectra import SpectrumModel, iter_mgf_spectra
from bijux_proteomics_foundation import JsonModel, hash_payload


class StreamingImportFormat(StrEnum):
    """Runtime-owned streaming import formats."""

    MGF = "mgf"
    MZML = "mzml"
    TSV = "tsv"


class StreamingImportRecord(JsonModel):
    """One accepted imported record preserved for reviewable subset checks."""

    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(..., min_length=1)
    fields: dict[str, str | int | float | None] = Field(default_factory=dict)


class StreamingImportBatch(JsonModel):
    """One bounded streaming batch emitted by a runtime import step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    format: StreamingImportFormat
    batch_index: int = Field(..., ge=1)
    record_count: int = Field(..., ge=0)
    records: tuple[StreamingImportRecord, ...] = Field(default_factory=tuple)


class StreamingImportStep(JsonModel):
    """One runtime-controlled streaming import step for a large input artifact."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    format: StreamingImportFormat
    batch_size: int = Field(default=500, ge=1, le=10_000)
    memory_limit_bytes: int = Field(..., ge=1)
    id_column: str | None = None
    selected_columns: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _validate_step(self) -> StreamingImportStep:
        if len(set(self.selected_columns)) != len(self.selected_columns):
            raise ValueError("streaming import selected_columns must be unique")
        return self


class StreamingImportReport(JsonModel):
    """Stable report over one completed streaming import step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    format: StreamingImportFormat
    source_path: str = Field(..., min_length=1)
    batch_size: int = Field(..., ge=1)
    batch_count: int = Field(..., ge=0)
    total_records: int = Field(..., ge=0)
    subset_limit: int = Field(..., ge=1)
    subset_records: tuple[StreamingImportRecord, ...] = Field(default_factory=tuple)
    subset_sha256: str = Field(..., min_length=64, max_length=64)
    peak_memory_bytes: int = Field(..., ge=0)
    memory_limit_bytes: int = Field(..., ge=1)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


def _spectrum_record(spectrum: SpectrumModel) -> StreamingImportRecord:
    return StreamingImportRecord(
        record_id=spectrum.spectrum_id,
        fields={
            "native_id": spectrum.native_id,
            "scan_number": spectrum.scan_number,
            "ms_level": spectrum.ms_level,
            "precursor_mz": spectrum.precursor_mz,
            "precursor_charge": spectrum.precursor_charge,
            "retention_time_seconds": spectrum.retention_time_seconds,
            "peak_count": len(spectrum.peaks),
        },
    )


def _iter_mgf_records(path: Path) -> Iterator[StreamingImportRecord]:
    for spectrum in iter_mgf_spectra(path):
        yield _spectrum_record(spectrum)


def _iter_mzml_records(path: Path) -> Iterator[StreamingImportRecord]:
    for spectrum in stream_mzml_spectra(path):
        yield _spectrum_record(spectrum)


def _resolve_tsv_record_id(
    row: dict[str, str],
    *,
    row_index: int,
    id_column: str | None,
) -> str:
    candidate_columns = ((id_column,) if id_column is not None else ()) + (
        "record_id",
        "spectrum_id",
        "sample_id",
        "peptide",
        "protein_id",
        "id",
    )
    for column in candidate_columns:
        value = row.get(column)
        if value is not None and value != "":
            return value
    return f"row-{row_index}"


def _iter_tsv_records(step: StreamingImportStep) -> Iterator[StreamingImportRecord]:
    path = Path(step.path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            return
        selected_columns = (
            tuple(reader.fieldnames)
            if not step.selected_columns
            else step.selected_columns
        )
        missing_columns = tuple(
            column for column in selected_columns if column not in reader.fieldnames
        )
        if missing_columns:
            raise ValueError(
                "streaming TSV import selected_columns are missing from the header: "
                + ", ".join(missing_columns)
            )
        for row_index, row in enumerate(reader, start=1):
            fields = {column: row.get(column) for column in selected_columns}
            yield StreamingImportRecord(
                record_id=_resolve_tsv_record_id(
                    row,
                    row_index=row_index,
                    id_column=step.id_column,
                ),
                fields=fields,
            )


def _iter_records(step: StreamingImportStep) -> Iterator[StreamingImportRecord]:
    path = Path(step.path)
    if step.format is StreamingImportFormat.MGF:
        yield from _iter_mgf_records(path)
        return
    if step.format is StreamingImportFormat.MZML:
        yield from _iter_mzml_records(path)
        return
    yield from _iter_tsv_records(step)


def iter_streaming_import_batches(
    step: StreamingImportStep,
) -> Iterator[StreamingImportBatch]:
    """Yield accepted records in bounded reviewable batches."""

    records: list[StreamingImportRecord] = []
    batch_index = 0
    for record in _iter_records(step):
        records.append(record)
        if len(records) < step.batch_size:
            continue
        batch_index += 1
        yield StreamingImportBatch(
            step_id=step.step_id,
            format=step.format,
            batch_index=batch_index,
            record_count=len(records),
            records=tuple(records),
        )
        records = []
    if records:
        batch_index += 1
        yield StreamingImportBatch(
            step_id=step.step_id,
            format=step.format,
            batch_index=batch_index,
            record_count=len(records),
            records=tuple(records),
        )


def run_streaming_import_step(
    step: StreamingImportStep,
    *,
    subset_limit: int = 25,
) -> StreamingImportReport:
    """Execute one streaming import step under a fixed memory ceiling."""

    if subset_limit < 1:
        raise ValueError("subset_limit must be >= 1")

    was_tracing = tracemalloc.is_tracing()
    if not was_tracing:
        tracemalloc.start()
    tracemalloc.reset_peak()
    try:
        batch_count = 0
        total_records = 0
        subset_records: list[StreamingImportRecord] = []
        for batch in iter_streaming_import_batches(step):
            batch_count += 1
            total_records += batch.record_count
            remaining = subset_limit - len(subset_records)
            if remaining > 0:
                subset_records.extend(batch.records[:remaining])
        peak_memory_bytes = tracemalloc.get_traced_memory()[1]
    finally:
        if not was_tracing and tracemalloc.is_tracing():
            tracemalloc.stop()

    if peak_memory_bytes > step.memory_limit_bytes:
        raise MemoryError(
            f"streaming import step {step.step_id!r} exceeded the memory limit "
            f"({peak_memory_bytes} > {step.memory_limit_bytes})"
        )

    subset_tuple = tuple(subset_records)
    return StreamingImportReport(
        step_id=step.step_id,
        format=step.format,
        source_path=step.path,
        batch_size=step.batch_size,
        batch_count=batch_count,
        total_records=total_records,
        subset_limit=subset_limit,
        subset_records=subset_tuple,
        subset_sha256=hash_payload(
            {"records": tuple(record.to_dict() for record in subset_tuple)}
        ),
        peak_memory_bytes=peak_memory_bytes,
        memory_limit_bytes=step.memory_limit_bytes,
        diagnostics=(
            "accepted records are processed in bounded streaming batches",
            "subset_sha256 covers the first accepted records in source order",
            (
                "MGF and mzML rejection accounting remains with the core scientific "
                "parse reports while runtime streaming preserves accepted import order"
                if step.format is not StreamingImportFormat.TSV
                else "TSV rows are streamed through DictReader without whole-file materialization"
            ),
        ),
    )
