# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""mzML, format-detection, and normalized run-bundle contracts."""

from __future__ import annotations

import base64
from collections.abc import Iterator
import csv
from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
import struct
from typing import Any
import zlib

from defusedxml import ElementTree as ET
from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import load_modification_registry
from bijux_proteomics.identification import (
    PsmRecord,
    SearchResultColumnMapping,
    build_psm_summary_report,
    export_psm_jsonl,
    parse_psm_tsv,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.spectra import (
    MgfParseReport,
    SpectrumCollectionSummary,
    SpectrumModel,
    SpectrumPeak,
    build_spectrum_collection_summary,
    parse_mgf,
    render_mgf,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel

_NS_MZML = "http://psi.hupo.org/ms/mzml"

_CV_MZ_ARRAY = "MS:1000514"
_CV_INTENSITY_ARRAY = "MS:1000515"
_CV_FLOAT32 = "MS:1000521"
_CV_FLOAT64 = "MS:1000523"
_CV_ZLIB = "MS:1000574"
_CV_NO_COMPRESSION = "MS:1000576"
_CV_INT32 = "MS:1000519"
_CV_INT64 = "MS:1000522"
_CV_NUMPRESS_LINEAR = "MS:1002312"
_CV_NUMPRESS_PIC = "MS:1002313"
_CV_NUMPRESS_SLOF = "MS:1002314"
_CV_MS_LEVEL = "MS:1000511"
_CV_SCAN_START_TIME = "MS:1000016"
_CV_SELECTED_ION_MZ = "MS:1000744"
_CV_CHARGE_STATE = "MS:1000041"
_CV_ISOLATION_WINDOW_TARGET_MZ = "MS:1000827"


class ProteomicsFormatKind(StrEnum):
    """Supported top-level proteomics input kinds."""

    FASTA = "fasta"
    PSM = "psm"
    MGF = "mgf"
    MZML = "mzml"
    MOD_REGISTRY = "mod-registry"
    DESIGN_TABLE = "design-table"


class FormatValidationIssue(JsonModel):
    """One stable format-validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    field: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    record_id: str | None = None


class RejectedMzmlSpectrum(JsonModel):
    """One rejected mzML spectrum plus stable issues."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    issues: tuple[FormatValidationIssue, ...] = Field(default_factory=tuple)


class MzmlRunMetadata(JsonModel):
    """Stable metadata extracted from one mzML run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    start_time_iso: str | None = None
    instrument_configuration_ids: tuple[str, ...] = Field(default_factory=tuple)
    instrument_names: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=0)


class MzmlParseReport(JsonModel):
    """Result of parsing one mzML document."""

    model_config = ConfigDict(extra="forbid")

    total_spectra: int = Field(..., ge=0)
    accepted_spectra: tuple[SpectrumModel, ...] = Field(default_factory=tuple)
    rejected_spectra: tuple[RejectedMzmlSpectrum, ...] = Field(default_factory=tuple)
    metadata: MzmlRunMetadata


class ExperimentalDesignEntry(JsonModel):
    """One normalized experimental-design row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate: int = Field(..., ge=1)
    fraction: int = Field(..., ge=1)
    spectra_file: str = Field(..., min_length=1)
    identifications_file: str | None = None
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None

    @field_validator(
        "sample_id",
        "condition",
        "spectra_file",
        "identifications_file",
        "batch",
        "instrument",
        "search_engine",
        mode="before",
    )
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class ExperimentalDesignRejectedRow(JsonModel):
    """One rejected design-table row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[FormatValidationIssue, ...] = Field(default_factory=tuple)


class ExperimentalDesignReport(JsonModel):
    """Stable parse report for one experimental-design table."""

    model_config = ConfigDict(extra="forbid")

    accepted_entries: tuple[ExperimentalDesignEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[ExperimentalDesignRejectedRow, ...] = Field(
        default_factory=tuple
    )


class ProteomicsRunMetadata(JsonModel):
    """Harmonized metadata for one normalized proteomics run."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str | None = None
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    run_id: str | None = None
    acquisition_start_time_iso: str | None = None
    spectra_format: ProteomicsFormatKind | None = None
    identification_format: ProteomicsFormatKind | None = None
    spectra_source_path: str | None = None
    identifications_source_path: str | None = None


class SourceFileManifestEntry(JsonModel):
    """Stable source-file record for a normalized run bundle."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    detected_format: ProteomicsFormatKind
    sha256: str = Field(..., min_length=64, max_length=64)


class NormalizedRunBundleManifest(JsonModel):
    """Stable manifest for one normalized proteomics run bundle."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    metadata: ProteomicsRunMetadata
    source_files: tuple[SourceFileManifestEntry, ...] = Field(default_factory=tuple)
    generated_files: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    rejected_spectra: int = Field(..., ge=0)
    rejected_identification_rows: int = Field(..., ge=0)


class FormatValidationReport(JsonModel):
    """Stable validation report for one detected proteomics input."""

    model_config = ConfigDict(extra="forbid")

    input_path: str = Field(..., min_length=1)
    detected_format: ProteomicsFormatKind
    valid: bool
    issues: tuple[FormatValidationIssue, ...] = Field(default_factory=tuple)
    summary: dict[str, Any] = Field(default_factory=dict)


class FormatConversionTarget(StrEnum):
    """Supported normalized conversion targets."""

    MGF = "mgf"
    SPECTRA_JSONL = "spectra-jsonl"
    PSM_JSONL = "psm-jsonl"
    DESIGN_JSONL = "design-jsonl"


class FormatConversionReport(JsonModel):
    """Stable report for one conversion operation."""

    model_config = ConfigDict(extra="forbid")

    input_path: str = Field(..., min_length=1)
    output_path: str = Field(..., min_length=1)
    input_format: ProteomicsFormatKind
    target_format: FormatConversionTarget
    written_record_count: int = Field(..., ge=0)


@dataclass
class _MzmlAccumulator:
    run_id: str | None = None
    start_time_iso: str | None = None
    instrument_configuration_ids: list[str] = field(default_factory=list)
    instrument_names: list[str] = field(default_factory=list)
    total_spectra: int = 0
    rejected_spectra: list[RejectedMzmlSpectrum] = field(default_factory=list)


def _local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _strip_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _issue(
    code: str,
    message: str,
    *,
    field: str | None = None,
    line_number: int | None = None,
    record_id: str | None = None,
) -> FormatValidationIssue:
    return FormatValidationIssue(
        code=code,
        message=message,
        field=field,
        line_number=line_number,
        record_id=record_id,
    )


def _default_psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value=None,
        protein_refs="proteins",
    )


def _first_bytes_text(path: Path, limit: int = 4096) -> str:
    return path.read_bytes()[:limit].decode("utf-8", errors="ignore")


def _detect_delimiter(first_line: str) -> str:
    return "\t" if "\t" in first_line else ","


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_file_entry(
    path: Path, detected_format: ProteomicsFormatKind
) -> SourceFileManifestEntry:
    return SourceFileManifestEntry(
        path=str(path),
        detected_format=detected_format,
        sha256=_hash_file(path),
    )


def _build_document_schema(document_kind: str) -> DocumentSchema:
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def _scan_number_from_text(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"scan=(\d+)", value, flags=re.IGNORECASE)
    if match is not None:
        return int(match.group(1))
    if value.isdigit():
        return int(value)
    return None


def _parse_binary_values(
    binary_data_array: Any,
    *,
    expected_length: int | None,
    spectrum_id: str,
) -> tuple[str | None, tuple[float, ...] | None, list[FormatValidationIssue]]:
    issues: list[FormatValidationIssue] = []
    kind: str | None = None
    float_size = 8
    compressed = False
    binary_text = ""
    precision_accessions: list[str] = []
    compression_accessions: list[str] = []
    supported_precisions = {_CV_FLOAT32, _CV_FLOAT64}
    supported_compressions = {_CV_ZLIB, _CV_NO_COMPRESSION}
    for element in binary_data_array.iter():
        if _local_name(element.tag) == "cvParam":
            accession = element.attrib.get("accession")
            if accession == _CV_MZ_ARRAY:
                kind = "mz"
            elif accession == _CV_INTENSITY_ARRAY:
                kind = "intensity"
            elif accession == _CV_FLOAT32:
                float_size = 4
                precision_accessions.append(accession)
            elif accession == _CV_FLOAT64:
                float_size = 8
                precision_accessions.append(accession)
            elif accession in {_CV_INT32, _CV_INT64}:
                precision_accessions.append(accession)
            elif accession == _CV_ZLIB:
                compressed = True
                compression_accessions.append(accession)
            elif accession == _CV_NO_COMPRESSION:
                compressed = False
                compression_accessions.append(accession)
            elif accession in {
                _CV_NUMPRESS_LINEAR,
                _CV_NUMPRESS_PIC,
                _CV_NUMPRESS_SLOF,
            }:
                compression_accessions.append(accession)
        elif _local_name(element.tag) == "binary":
            binary_text = (element.text or "").strip()
    if kind is None:
        issues.append(
            _issue(
                "missing_binary_array_kind",
                "binaryDataArray is missing array-kind cvParam",
                record_id=spectrum_id,
            )
        )
        return None, None, issues
    if not precision_accessions:
        issues.append(
            _issue(
                "missing_binary_precision",
                "binaryDataArray is missing a floating-point precision cvParam",
                field=kind,
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    if len(set(precision_accessions)) > 1:
        issues.append(
            _issue(
                "conflicting_binary_precision",
                "binaryDataArray declares multiple precision encodings",
                field=kind,
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    precision_accession = precision_accessions[0]
    if precision_accession not in supported_precisions:
        issues.append(
            _issue(
                "unsupported_binary_precision",
                f"binaryDataArray precision {precision_accession} is not supported",
                field=kind,
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    if len(set(compression_accessions)) > 1:
        issues.append(
            _issue(
                "conflicting_binary_compression",
                "binaryDataArray declares multiple compression encodings",
                field=kind,
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    if compression_accessions and compression_accessions[0] not in supported_compressions:
        issues.append(
            _issue(
                "unsupported_binary_compression",
                f"binaryDataArray compression {compression_accessions[0]} is not supported",
                field=kind,
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    if not binary_text:
        issues.append(
            _issue(
                "missing_binary_payload",
                "binaryDataArray is missing encoded payload",
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    try:
        payload = base64.b64decode(binary_text)
        if compressed:
            payload = zlib.decompress(payload)
    except Exception as exc:  # noqa: BLE001
        issues.append(
            _issue(
                "invalid_binary_payload", str(exc), field=kind, record_id=spectrum_id
            )
        )
        return kind, None, issues
    if len(payload) % float_size != 0:
        issues.append(
            _issue(
                "invalid_binary_array_width",
                f"decoded payload width {len(payload)} is not divisible by {float_size}",
                field=kind,
                record_id=spectrum_id,
            )
        )
        return kind, None, issues
    count = len(payload) // float_size
    if expected_length is not None and count != expected_length:
        issues.append(
            _issue(
                "array_length_mismatch",
                f"binary array length {count} does not match defaultArrayLength {expected_length}",
                field=kind,
                record_id=spectrum_id,
            )
        )
    format_code = "f" if float_size == 4 else "d"
    values = struct.unpack("<" + format_code * count, payload)
    return kind, tuple(float(value) for value in values), issues


def _parse_time_seconds(scan_cv: Any) -> float | None:
    value = _strip_text(scan_cv.attrib.get("value"))
    if value is None:
        return None
    numeric = float(value)
    unit_name = (_strip_text(scan_cv.attrib.get("unitName")) or "").lower()
    if unit_name in {"minute", "minutes"}:
        return numeric * 60.0
    return numeric


def _parse_spectrum_element(
    spectrum: Any,
) -> tuple[SpectrumModel | None, list[FormatValidationIssue]]:
    spectrum_id = (
        spectrum.attrib.get("id") or f"index={spectrum.attrib.get('index', 'unknown')}"
    )
    issues: list[FormatValidationIssue] = []
    expected_length = int(spectrum.attrib.get("defaultArrayLength", "0") or "0")
    ms_level: int | None = None
    retention_time_seconds: float | None = None
    precursor_mz: float | None = None
    precursor_charge: int | None = None
    parent_spectrum_id: str | None = None
    product_isolation_mz: float | None = None
    mz_values: tuple[float, ...] | None = None
    intensity_values: tuple[float, ...] | None = None

    for element in spectrum.iter():
        if _local_name(element.tag) != "cvParam":
            continue
        accession = element.attrib.get("accession")
        if accession == _CV_MS_LEVEL:
            try:
                ms_level = int(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_ms_level",
                        str(exc),
                        field="ms_level",
                        record_id=spectrum_id,
                    )
                )
        elif accession == _CV_SCAN_START_TIME:
            try:
                retention_time_seconds = _parse_time_seconds(element)
            except ValueError as exc:
                issues.append(
                    _issue(
                        "invalid_scan_start_time",
                        str(exc),
                        field="scan_start_time",
                        record_id=spectrum_id,
                    )
                )
        elif accession == _CV_SELECTED_ION_MZ:
            try:
                precursor_mz = float(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_precursor_mz",
                        str(exc),
                        field="precursor_mz",
                        record_id=spectrum_id,
                    )
                )
        elif accession == _CV_CHARGE_STATE:
            try:
                precursor_charge = int(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_precursor_charge",
                        str(exc),
                        field="precursor_charge",
                        record_id=spectrum_id,
                    )
                )

    for precursor in spectrum.iter():
        if _local_name(precursor.tag) != "precursor":
            continue
        parent_spectrum_id = _strip_text(precursor.attrib.get("spectrumRef"))
        break

    for product in spectrum.iter():
        if _local_name(product.tag) != "product":
            continue
        for cv_param in product.iter():
            if _local_name(cv_param.tag) != "cvParam":
                continue
            if cv_param.attrib.get("accession") != _CV_ISOLATION_WINDOW_TARGET_MZ:
                continue
            try:
                product_isolation_mz = float(cv_param.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_product_isolation_mz",
                        str(exc),
                        field="product_isolation_mz",
                        record_id=spectrum_id,
                    )
                )
            break
        break

    for binary_data_array in spectrum.iter():
        if _local_name(binary_data_array.tag) != "binaryDataArray":
            continue
        kind, values, value_issues = _parse_binary_values(
            binary_data_array,
            expected_length=expected_length if expected_length else None,
            spectrum_id=spectrum_id,
        )
        issues.extend(value_issues)
        if kind == "mz":
            mz_values = values
        elif kind == "intensity":
            intensity_values = values

    if precursor_mz is None:
        issues.append(
            _issue(
                "missing_precursor_mz",
                "mzML spectrum is missing selected ion m/z",
                field="precursor_mz",
                record_id=spectrum_id,
            )
        )
    if mz_values is None:
        issues.append(
            _issue(
                "missing_mz_array",
                "mzML spectrum is missing an m/z array",
                field="mz",
                record_id=spectrum_id,
            )
        )
    if intensity_values is None:
        issues.append(
            _issue(
                "missing_intensity_array",
                "mzML spectrum is missing an intensity array",
                field="intensity",
                record_id=spectrum_id,
            )
        )
    if (
        mz_values is not None
        and intensity_values is not None
        and len(mz_values) != len(intensity_values)
    ):
        issues.append(
            _issue(
                "peak_array_length_mismatch",
                f"m/z array length {len(mz_values)} does not match intensity array length {len(intensity_values)}",
                record_id=spectrum_id,
            )
        )
    if issues:
        return None, issues
    peaks = tuple(
        SpectrumPeak(mz=mz, intensity=intensity)
        for mz, intensity in zip(mz_values or (), intensity_values or (), strict=True)
    )
    return (
        SpectrumModel(
            spectrum_id=spectrum_id,
            native_id=spectrum_id,
            scan_number=_scan_number_from_text(spectrum_id),
            ms_level=ms_level,
            parent_spectrum_id=parent_spectrum_id,
            product_isolation_mz=product_isolation_mz,
            precursor_mz=precursor_mz or 1.0,
            precursor_charge=precursor_charge,
            retention_time_seconds=retention_time_seconds,
            peaks=peaks,
            title=spectrum.attrib.get("id"),
        ),
        [],
    )


def _instrument_name(instrument_configuration: Any) -> str | None:
    for child in instrument_configuration.iter():
        if _local_name(child.tag) != "cvParam":
            continue
        name = _strip_text(child.attrib.get("name"))
        if name:
            return name
    return None


def _iter_mzml_spectra(
    path: Path, accumulator: _MzmlAccumulator
) -> Iterator[SpectrumModel]:
    for event, element in ET.iterparse(path, events=("start", "end")):
        tag = _local_name(element.tag)
        if event == "start" and tag == "run":
            accumulator.run_id = _strip_text(element.attrib.get("id"))
            accumulator.start_time_iso = _strip_text(
                element.attrib.get("startTimeStamp")
            )
            continue
        if event == "end" and tag == "instrumentConfiguration":
            configuration_id = _strip_text(element.attrib.get("id"))
            if (
                configuration_id
                and configuration_id not in accumulator.instrument_configuration_ids
            ):
                accumulator.instrument_configuration_ids.append(configuration_id)
            instrument_name = _instrument_name(element)
            if instrument_name and instrument_name not in accumulator.instrument_names:
                accumulator.instrument_names.append(instrument_name)
            element.clear()
            continue
        if event == "end" and tag == "spectrum":
            accumulator.total_spectra += 1
            spectrum, issues = _parse_spectrum_element(element)
            if spectrum is None:
                spectrum_id = (
                    element.attrib.get("id")
                    or f"index={element.attrib.get('index', 'unknown')}"
                )
                accumulator.rejected_spectra.append(
                    RejectedMzmlSpectrum(spectrum_id=spectrum_id, issues=tuple(issues))
                )
            else:
                yield spectrum
            element.clear()


def parse_mzml(path: Path) -> MzmlParseReport:
    """Parse a small or medium mzML file into stable spectrum contracts."""
    accumulator = _MzmlAccumulator()
    accepted_spectra = tuple(_iter_mzml_spectra(path, accumulator))
    metadata = MzmlRunMetadata(
        run_id=accumulator.run_id,
        start_time_iso=accumulator.start_time_iso,
        instrument_configuration_ids=tuple(accumulator.instrument_configuration_ids),
        instrument_names=tuple(accumulator.instrument_names),
        spectrum_count=accumulator.total_spectra,
    )
    return MzmlParseReport(
        total_spectra=accumulator.total_spectra,
        accepted_spectra=accepted_spectra,
        rejected_spectra=tuple(accumulator.rejected_spectra),
        metadata=metadata,
    )


def stream_mzml_spectra(path: Path) -> Iterator[SpectrumModel]:
    """Stream accepted spectra from one mzML document."""
    accumulator = _MzmlAccumulator()
    yield from _iter_mzml_spectra(path, accumulator)


def extract_mzml_metadata(path: Path) -> MzmlRunMetadata:
    """Extract stable run metadata from one mzML document."""
    return parse_mzml(path).metadata


def build_mzml_collection_summary(
    parse_report: MzmlParseReport,
) -> SpectrumCollectionSummary:
    """Build a compact summary for one parsed mzML run."""
    counts_by_charge: dict[str, int] = {}
    issue_counts: dict[str, int] = {}
    total_peak_count = 0
    for spectrum in parse_report.accepted_spectra:
        total_peak_count += len(spectrum.peaks)
        key = (
            "unknown"
            if spectrum.precursor_charge is None
            else str(spectrum.precursor_charge)
        )
        counts_by_charge[key] = counts_by_charge.get(key, 0) + 1
    for rejected in parse_report.rejected_spectra:
        for issue in rejected.issues:
            issue_counts[issue.code] = issue_counts.get(issue.code, 0) + 1
    spectrum_count = len(parse_report.accepted_spectra)
    return SpectrumCollectionSummary(
        spectrum_count=spectrum_count,
        rejected_block_count=len(parse_report.rejected_spectra),
        total_peak_count=total_peak_count,
        average_peak_count=(total_peak_count / spectrum_count)
        if spectrum_count
        else 0.0,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        issue_counts=dict(sorted(issue_counts.items())),
    )


def export_spectra_jsonl(spectra: tuple[SpectrumModel, ...], path: Path) -> None:
    """Write normalized spectra as stable JSONL."""
    with path.open("w", encoding="utf-8") as handle:
        for spectrum in spectra:
            handle.write(
                json.dumps(spectrum.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def detect_proteomics_format(path: Path) -> ProteomicsFormatKind:
    """Detect the most likely proteomics format from file name and content."""
    suffix = path.suffix.lower()
    if suffix in {".fasta", ".fa", ".faa"}:
        return ProteomicsFormatKind.FASTA
    if suffix == ".mgf":
        return ProteomicsFormatKind.MGF
    if suffix == ".mzml":
        return ProteomicsFormatKind.MZML
    if path.name.endswith(".design.tsv") or path.name.endswith(".design.csv"):
        return ProteomicsFormatKind.DESIGN_TABLE
    text = _first_bytes_text(path)
    stripped = text.lstrip()
    if "<mzML" in text or f"{{{_NS_MZML}}}" in text:
        return ProteomicsFormatKind.MZML
    if stripped.startswith("BEGIN IONS"):
        return ProteomicsFormatKind.MGF
    if stripped.startswith(">"):
        return ProteomicsFormatKind.FASTA
    if suffix == ".json" and (
        '"static_modifications"' in text or '"variable_modifications"' in text
    ):
        return ProteomicsFormatKind.MOD_REGISTRY
    header = stripped.splitlines()[0] if stripped.splitlines() else ""
    header_columns = {
        column.strip()
        for column in header.split(_detect_delimiter(header))
        if column.strip()
    }
    if {"sample_id", "condition", "replicate", "fraction", "spectra_file"}.issubset(
        header_columns
    ):
        return ProteomicsFormatKind.DESIGN_TABLE
    if {"spectrum_id", "peptide", "charge", "score"}.issubset(header_columns):
        return ProteomicsFormatKind.PSM
    raise ValueError(f"could not detect proteomics format for {path.name!r}")


def parse_experimental_design_table(path: Path) -> ExperimentalDesignReport:
    """Parse one experimental-design TSV or CSV table."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return ExperimentalDesignReport()
    delimiter = _detect_delimiter(lines[0])
    reader = csv.DictReader(lines, delimiter=delimiter)
    accepted_entries: list[ExperimentalDesignEntry] = []
    rejected_rows: list[ExperimentalDesignRejectedRow] = []
    required_fields = {
        "sample_id",
        "condition",
        "replicate",
        "fraction",
        "spectra_file",
    }
    header_fields = set(reader.fieldnames or [])
    missing_fields = required_fields - header_fields
    if missing_fields:
        header_issues = tuple(
            _issue(
                "missing_design_column",
                f"design table is missing required column {field!r}",
                field=field,
                line_number=1,
            )
            for field in sorted(missing_fields)
        )
        return ExperimentalDesignReport(
            accepted_entries=(),
            rejected_rows=(
                ExperimentalDesignRejectedRow(
                    row_number=1,
                    values={},
                    issues=header_issues,
                ),
            ),
        )

    for row_number, row in enumerate(reader, start=2):
        values = {
            key: (value or "").strip() for key, value in row.items() if key is not None
        }
        issues: list[FormatValidationIssue] = []
        for field_name in sorted(required_fields):
            if not values.get(field_name):
                issues.append(
                    _issue(
                        "missing_design_value",
                        f"design table row is missing required value for {field_name!r}",
                        field=field_name,
                        line_number=row_number,
                    )
                )
        try:
            entry = ExperimentalDesignEntry(
                sample_id=values.get("sample_id") or "",
                condition=values.get("condition") or "",
                replicate=int(values.get("replicate") or "0"),
                fraction=int(values.get("fraction") or "0"),
                spectra_file=values.get("spectra_file") or "",
                identifications_file=values.get("identifications_file"),
                batch=values.get("batch"),
                instrument=values.get("instrument"),
                search_engine=values.get("search_engine"),
            )
        except Exception as exc:  # noqa: BLE001
            issues.append(
                _issue(
                    "invalid_design_row",
                    str(exc),
                    line_number=row_number,
                )
            )
            entry = None
        if issues or entry is None:
            rejected_rows.append(
                ExperimentalDesignRejectedRow(
                    row_number=row_number,
                    values=values,
                    issues=tuple(issues),
                )
            )
            continue
        accepted_entries.append(entry)
    return ExperimentalDesignReport(
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
    )


def harmonize_run_metadata(
    *,
    mzml_metadata: MzmlRunMetadata | None = None,
    design_entry: ExperimentalDesignEntry | None = None,
    spectra_format: ProteomicsFormatKind | None = None,
    identification_format: ProteomicsFormatKind | None = None,
    spectra_source_path: Path | None = None,
    identifications_source_path: Path | None = None,
) -> ProteomicsRunMetadata:
    """Build one harmonized run metadata document."""
    return ProteomicsRunMetadata(
        sample_id=design_entry.sample_id if design_entry is not None else None,
        condition=design_entry.condition if design_entry is not None else None,
        replicate=design_entry.replicate if design_entry is not None else None,
        fraction=design_entry.fraction if design_entry is not None else None,
        batch=design_entry.batch if design_entry is not None else None,
        instrument=(
            design_entry.instrument
            if design_entry is not None and design_entry.instrument is not None
            else (
                mzml_metadata.instrument_names[0]
                if mzml_metadata and mzml_metadata.instrument_names
                else None
            )
        ),
        search_engine=design_entry.search_engine if design_entry is not None else None,
        run_id=mzml_metadata.run_id if mzml_metadata is not None else None,
        acquisition_start_time_iso=mzml_metadata.start_time_iso
        if mzml_metadata is not None
        else None,
        spectra_format=spectra_format,
        identification_format=identification_format,
        spectra_source_path=str(spectra_source_path)
        if spectra_source_path is not None
        else None,
        identifications_source_path=(
            str(identifications_source_path)
            if identifications_source_path is not None
            else None
        ),
    )


def validate_proteomics_input(
    path: Path,
    *,
    input_kind: ProteomicsFormatKind | None = None,
) -> FormatValidationReport:
    """Validate one proteomics input under a detected or declared format kind."""
    resolved_kind = input_kind or detect_proteomics_format(path)
    issues: list[FormatValidationIssue] = []
    summary: dict[str, Any] = {}
    if resolved_kind is ProteomicsFormatKind.FASTA:
        fasta_report = parse_fasta_document(
            path.read_text(), mode=FastaParseMode.STRICT
        )
        for rejected_record in fasta_report.rejected_records:
            issues.append(
                _issue(
                    "rejected_fasta_record",
                    "; ".join(issue.message for issue in rejected_record.issues),
                    record_id=rejected_record.source_identifier,
                )
            )
        summary = {
            "accepted_records": len(fasta_report.accepted_records),
            "rejected_records": len(fasta_report.rejected_records),
        }
    elif resolved_kind is ProteomicsFormatKind.PSM:
        psm_report = parse_psm_tsv(path, mapping=_default_psm_mapping())
        for rejected_row in psm_report.rejected_rows:
            issues.append(
                _issue(
                    "rejected_psm_row",
                    "; ".join(issue.message for issue in rejected_row.issues),
                    line_number=rejected_row.row_number,
                )
            )
        summary = {
            "accepted_rows": len(psm_report.accepted_records),
            "rejected_rows": len(psm_report.rejected_rows),
        }
    elif resolved_kind is ProteomicsFormatKind.MGF:
        mgf_report: MgfParseReport = parse_mgf(path)
        for block in mgf_report.rejected_blocks:
            for issue in block.issues:
                issues.append(
                    _issue(
                        issue.code,
                        issue.message,
                        field=issue.field,
                        line_number=issue.line_number,
                        record_id=block.title or f"block-{block.block_index}",
                    )
                )
        summary = build_spectrum_collection_summary(mgf_report).to_dict()
    elif resolved_kind is ProteomicsFormatKind.MZML:
        mzml_report = parse_mzml(path)
        for rejected_spectrum in mzml_report.rejected_spectra:
            issues.extend(rejected_spectrum.issues)
        summary = {
            "metadata": mzml_report.metadata.to_dict(),
            "summary": build_mzml_collection_summary(mzml_report).to_dict(),
        }
    elif resolved_kind is ProteomicsFormatKind.MOD_REGISTRY:
        registry = load_modification_registry(path)
        summary = {
            "static_modifications": len(registry.static_modifications),
            "variable_modifications": len(registry.variable_modifications),
        }
    else:
        design_report = parse_experimental_design_table(path)
        for design_rejected_row in design_report.rejected_rows:
            issues.extend(design_rejected_row.issues)
        summary = {
            "accepted_entries": len(design_report.accepted_entries),
            "rejected_rows": len(design_report.rejected_rows),
        }
    return FormatValidationReport(
        input_path=str(path),
        detected_format=resolved_kind,
        valid=len(issues) == 0,
        issues=tuple(issues),
        summary=summary,
    )


def convert_proteomics_format(
    *,
    input_path: Path,
    output_path: Path,
    input_kind: ProteomicsFormatKind | None = None,
    target_format: FormatConversionTarget,
) -> FormatConversionReport:
    """Convert one supported input into a normalized Bijux output table."""
    resolved_kind = input_kind or detect_proteomics_format(input_path)
    if target_format is FormatConversionTarget.MGF:
        if resolved_kind is not ProteomicsFormatKind.MZML:
            raise ValueError("mgf conversion currently supports only mzML input")
        report = parse_mzml(input_path)
        output_path.write_text(render_mgf(report.accepted_spectra), encoding="utf-8")
        written_record_count = len(report.accepted_spectra)
    elif target_format is FormatConversionTarget.SPECTRA_JSONL:
        if resolved_kind is ProteomicsFormatKind.MZML:
            spectra = parse_mzml(input_path).accepted_spectra
        elif resolved_kind is ProteomicsFormatKind.MGF:
            spectra = parse_mgf(input_path).accepted_spectra
        else:
            raise ValueError("spectra-jsonl conversion requires mzML or MGF input")
        export_spectra_jsonl(spectra, output_path)
        written_record_count = len(spectra)
    elif target_format is FormatConversionTarget.PSM_JSONL:
        if resolved_kind is not ProteomicsFormatKind.PSM:
            raise ValueError("psm-jsonl conversion requires PSM TSV input")
        records: tuple[PsmRecord, ...] = parse_psm_tsv(
            input_path, mapping=_default_psm_mapping()
        ).accepted_records
        export_psm_jsonl(records, output_path)
        written_record_count = len(records)
    else:
        if resolved_kind is not ProteomicsFormatKind.DESIGN_TABLE:
            raise ValueError("design-jsonl conversion requires a design-table input")
        design_report = parse_experimental_design_table(input_path)
        with output_path.open("w", encoding="utf-8") as handle:
            for entry in design_report.accepted_entries:
                handle.write(
                    json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
                )
                handle.write("\n")
        written_record_count = len(design_report.accepted_entries)
    return FormatConversionReport(
        input_path=str(input_path),
        output_path=str(output_path),
        input_format=resolved_kind,
        target_format=target_format,
        written_record_count=written_record_count,
    )


def build_normalized_run_bundle(
    *,
    bundle_dir: Path,
    spectra_path: Path,
    identifications_path: Path | None = None,
    design_path: Path | None = None,
) -> NormalizedRunBundleManifest:
    """Build one normalized run bundle directory with spectra, IDs, and metadata."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    spectra_kind = detect_proteomics_format(spectra_path)
    if spectra_kind not in {ProteomicsFormatKind.MGF, ProteomicsFormatKind.MZML}:
        raise ValueError("run bundle spectra input must be mzML or MGF")

    generated_files: list[str] = []
    source_files: list[SourceFileManifestEntry] = [
        _source_file_entry(spectra_path, spectra_kind)
    ]
    rejected_spectra = 0
    mzml_metadata: MzmlRunMetadata | None = None

    if spectra_kind is ProteomicsFormatKind.MZML:
        spectra_report = parse_mzml(spectra_path)
        accepted_spectra = spectra_report.accepted_spectra
        rejected_spectra = len(spectra_report.rejected_spectra)
        mzml_metadata = spectra_report.metadata
    else:
        mgf_report = parse_mgf(spectra_path)
        accepted_spectra = mgf_report.accepted_spectra
        rejected_spectra = len(mgf_report.rejected_blocks)

    spectra_output_path = bundle_dir / "spectra.normalized.mgf"
    spectra_output_path.write_text(render_mgf(accepted_spectra), encoding="utf-8")
    generated_files.append(spectra_output_path.name)

    spectra_validation_path = bundle_dir / "spectra.validation.json"
    spectra_validation = validate_proteomics_input(
        spectra_path, input_kind=spectra_kind
    )
    spectra_validation_path.write_text(
        spectra_validation.to_stable_json() + "\n", encoding="utf-8"
    )
    generated_files.append(spectra_validation_path.name)

    psm_count = 0
    rejected_identification_rows = 0
    identification_kind: ProteomicsFormatKind | None = None
    if identifications_path is not None:
        identification_kind = detect_proteomics_format(identifications_path)
        if identification_kind is not ProteomicsFormatKind.PSM:
            raise ValueError(
                "run bundle identification input must be a normalized or generic PSM TSV"
            )
        source_files.append(
            _source_file_entry(identifications_path, identification_kind)
        )
        psm_report = parse_psm_tsv(identifications_path, mapping=_default_psm_mapping())
        psm_count = len(psm_report.accepted_records)
        rejected_identification_rows = len(psm_report.rejected_rows)
        psm_output_path = bundle_dir / "identifications.normalized.jsonl"
        export_psm_jsonl(psm_report.accepted_records, psm_output_path)
        generated_files.append(psm_output_path.name)
        psm_summary_path = bundle_dir / "identifications.summary.json"
        psm_summary = build_psm_summary_report(psm_report.accepted_records)
        psm_summary_path.write_text(
            psm_summary.to_stable_json() + "\n", encoding="utf-8"
        )
        generated_files.append(psm_summary_path.name)

    design_entry: ExperimentalDesignEntry | None = None
    if design_path is not None:
        design_kind = detect_proteomics_format(design_path)
        if design_kind is not ProteomicsFormatKind.DESIGN_TABLE:
            raise ValueError("run bundle design input must be a design table")
        source_files.append(_source_file_entry(design_path, design_kind))
        design_report = parse_experimental_design_table(design_path)
        if design_report.accepted_entries:
            design_entry = design_report.accepted_entries[0]
        design_output_path = bundle_dir / "design.normalized.jsonl"
        with design_output_path.open("w", encoding="utf-8") as handle:
            for entry in design_report.accepted_entries:
                handle.write(
                    json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
                )
                handle.write("\n")
        generated_files.append(design_output_path.name)

    metadata = harmonize_run_metadata(
        mzml_metadata=mzml_metadata,
        design_entry=design_entry,
        spectra_format=spectra_kind,
        identification_format=identification_kind,
        spectra_source_path=spectra_path,
        identifications_source_path=identifications_path,
    )
    metadata_path = bundle_dir / "run.metadata.json"
    metadata_path.write_text(metadata.to_stable_json() + "\n", encoding="utf-8")
    generated_files.append(metadata_path.name)

    schema = _build_document_schema("normalized_proteomics_run_bundle")
    manifest = NormalizedRunBundleManifest(
        document_schema=schema,
        metadata=metadata,
        source_files=tuple(source_files),
        generated_files=tuple(generated_files),
        spectrum_count=len(accepted_spectra),
        psm_count=psm_count,
        rejected_spectra=rejected_spectra,
        rejected_identification_rows=rejected_identification_rows,
    )
    manifest = manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )
    manifest_path = bundle_dir / "bundle.manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")
    return manifest
