# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Practical mzML reader for spectra, chromatograms, and decoding support."""

from __future__ import annotations

import base64
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
import re
import struct
from typing import Any
import zlib

from defusedxml import ElementTree as ET
from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats.format_validation import FormatValidationIssue
from bijux_proteomics.io.spectra import (
    SpectrumCollectionSummary,
    SpectrumModel,
    SpectrumPeak,
)
from bijux_proteomics_foundation import JsonModel

_CV_MZ_ARRAY = "MS:1000514"
_CV_INTENSITY_ARRAY = "MS:1000515"
_CV_TIME_ARRAY = "MS:1000595"
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
_CV_SELECTED_ION_INTENSITY = "MS:1000042"
_CV_ISOLATION_WINDOW_TARGET_MZ = "MS:1000827"
_CV_ISOLATION_WINDOW_LOWER_OFFSET = "MS:1000828"
_CV_ISOLATION_WINDOW_UPPER_OFFSET = "MS:1000829"
_CV_TOTAL_ION_CURRENT_CHROMATOGRAM = "MS:1000235"
_CV_BASE_PEAK_CHROMATOGRAM = "MS:1000628"


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


class RejectedMzmlChromatogram(JsonModel):
    """One rejected mzML chromatogram plus stable issues."""

    model_config = ConfigDict(extra="forbid")

    chromatogram_id: str = Field(..., min_length=1)
    issues: tuple[FormatValidationIssue, ...] = Field(default_factory=tuple)


class MzmlChromatogramPoint(JsonModel):
    """One mzML chromatogram time or intensity point."""

    model_config = ConfigDict(extra="forbid")

    time_seconds: float = Field(..., ge=0.0)
    intensity: float = Field(..., ge=0.0)


class MzmlChromatogramTrace(JsonModel):
    """One accepted chromatogram trace from mzML."""

    model_config = ConfigDict(extra="forbid")

    chromatogram_id: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    point_count: int = Field(..., ge=0)
    points: tuple[MzmlChromatogramPoint, ...] = Field(default_factory=tuple)


class MzmlChromatogramReport(JsonModel):
    """Stable mzML chromatogram extraction report."""

    model_config = ConfigDict(extra="forbid")

    total_chromatograms: int = Field(..., ge=0)
    accepted_traces: tuple[MzmlChromatogramTrace, ...] = Field(default_factory=tuple)
    rejected_chromatograms: tuple[RejectedMzmlChromatogram, ...] = Field(
        default_factory=tuple
    )


class MzmlDecodingSupportReport(JsonModel):
    """Decoding capability report over one mzML binary-array surface."""

    model_config = ConfigDict(extra="forbid")

    supported: bool
    spectrum_count: int = Field(..., ge=0)
    accepted_spectrum_count: int = Field(..., ge=0)
    rejected_spectrum_count: int = Field(..., ge=0)
    compression_accessions: tuple[str, ...] = Field(default_factory=tuple)
    precision_accessions: tuple[str, ...] = Field(default_factory=tuple)
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


class MzmlPracticalReviewReport(JsonModel):
    """Practical review packet over one mzML run."""

    model_config = ConfigDict(extra="forbid")

    metadata: MzmlRunMetadata
    summary: dict[str, Any] = Field(default_factory=dict)
    decoding_support: MzmlDecodingSupportReport
    chromatograms: MzmlChromatogramReport
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


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


def _scan_number_from_text(value: str | None) -> int | None:
    if value is None:
        return None
    for pattern in (r"scan=(\d+)", r"scanId=(\d+)", r"index=(\d+)"):
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    digits = "".join(character for character in value if character.isdigit())
    return int(digits) if digits else None


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
            elif accession == _CV_TIME_ARRAY:
                kind = "time"
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
    if (
        compression_accessions
        and compression_accessions[0] not in supported_compressions
    ):
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
    precursor_intensity: float | None = None
    precursor_charge: int | None = None
    isolation_window_target_mz: float | None = None
    isolation_window_lower_offset: float | None = None
    isolation_window_upper_offset: float | None = None
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
        elif accession == _CV_SELECTED_ION_INTENSITY:
            try:
                precursor_intensity = float(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_precursor_intensity",
                        str(exc),
                        field="precursor_intensity",
                        record_id=spectrum_id,
                    )
                )
        elif accession == _CV_ISOLATION_WINDOW_TARGET_MZ:
            try:
                isolation_window_target_mz = float(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_isolation_window_target_mz",
                        str(exc),
                        field="isolation_window_target_mz",
                        record_id=spectrum_id,
                    )
                )
        elif accession == _CV_ISOLATION_WINDOW_LOWER_OFFSET:
            try:
                isolation_window_lower_offset = float(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_isolation_window_lower_offset",
                        str(exc),
                        field="isolation_window_lower_offset",
                        record_id=spectrum_id,
                    )
                )
        elif accession == _CV_ISOLATION_WINDOW_UPPER_OFFSET:
            try:
                isolation_window_upper_offset = float(element.attrib["value"])
            except (KeyError, ValueError) as exc:
                issues.append(
                    _issue(
                        "invalid_isolation_window_upper_offset",
                        str(exc),
                        field="isolation_window_upper_offset",
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
            isolation_window_target_mz=isolation_window_target_mz,
            isolation_window_lower_offset=isolation_window_lower_offset,
            isolation_window_upper_offset=isolation_window_upper_offset,
            product_isolation_mz=product_isolation_mz,
            precursor_mz=precursor_mz or 1.0,
            precursor_intensity=precursor_intensity,
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


def _parse_chromatogram_element(
    chromatogram: Any,
) -> tuple[MzmlChromatogramTrace | None, list[FormatValidationIssue]]:
    chromatogram_id = (
        chromatogram.attrib.get("id")
        or f"index={chromatogram.attrib.get('index', 'unknown')}"
    )
    issues: list[FormatValidationIssue] = []
    expected_length = int(chromatogram.attrib.get("defaultArrayLength", "0") or "0")
    trace_kind = "other"
    time_values: tuple[float, ...] | None = None
    intensity_values: tuple[float, ...] | None = None

    for element in chromatogram.iter():
        if _local_name(element.tag) != "cvParam":
            continue
        accession = element.attrib.get("accession")
        if accession == _CV_TOTAL_ION_CURRENT_CHROMATOGRAM:
            trace_kind = "tic"
        elif accession == _CV_BASE_PEAK_CHROMATOGRAM:
            trace_kind = "bpc"

    for binary_data_array in chromatogram.iter():
        if _local_name(binary_data_array.tag) != "binaryDataArray":
            continue
        kind, values, value_issues = _parse_binary_values(
            binary_data_array,
            expected_length=expected_length if expected_length else None,
            spectrum_id=chromatogram_id,
        )
        issues.extend(value_issues)
        if kind == "time":
            time_values = values
        elif kind == "intensity":
            intensity_values = values

    if time_values is None:
        issues.append(
            _issue(
                "missing_time_array",
                "mzML chromatogram is missing a time array",
                field="time",
                record_id=chromatogram_id,
            )
        )
    if intensity_values is None:
        issues.append(
            _issue(
                "missing_intensity_array",
                "mzML chromatogram is missing an intensity array",
                field="intensity",
                record_id=chromatogram_id,
            )
        )
    if (
        time_values is not None
        and intensity_values is not None
        and len(time_values) != len(intensity_values)
    ):
        issues.append(
            _issue(
                "chromatogram_array_length_mismatch",
                f"time array length {len(time_values)} does not match intensity array length {len(intensity_values)}",
                record_id=chromatogram_id,
            )
        )
    if issues:
        return None, issues

    points = tuple(
        MzmlChromatogramPoint(time_seconds=time_value, intensity=intensity_value)
        for time_value, intensity_value in zip(
            time_values or (),
            intensity_values or (),
            strict=True,
        )
    )
    return (
        MzmlChromatogramTrace(
            chromatogram_id=chromatogram_id,
            kind=trace_kind,
            point_count=len(points),
            points=points,
        ),
        [],
    )


def extract_mzml_chromatograms(path: Path) -> MzmlChromatogramReport:
    """Extract TIC/BPC and other chromatogram traces from one mzML document."""

    accepted_traces: list[MzmlChromatogramTrace] = []
    rejected_chromatograms: list[RejectedMzmlChromatogram] = []
    total_chromatograms = 0

    for _event, element in ET.iterparse(path, events=("end",)):
        if _local_name(element.tag) != "chromatogram":
            continue
        total_chromatograms += 1
        trace, issues = _parse_chromatogram_element(element)
        chromatogram_id = (
            element.attrib.get("id")
            or f"index={element.attrib.get('index', 'unknown')}"
        )
        if trace is None:
            rejected_chromatograms.append(
                RejectedMzmlChromatogram(
                    chromatogram_id=chromatogram_id,
                    issues=tuple(issues),
                )
            )
        else:
            accepted_traces.append(trace)
        element.clear()

    return MzmlChromatogramReport(
        total_chromatograms=total_chromatograms,
        accepted_traces=tuple(accepted_traces),
        rejected_chromatograms=tuple(rejected_chromatograms),
    )


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
    average_peak_count = (
        float(total_peak_count) / float(spectrum_count) if spectrum_count else 0.0
    )
    return SpectrumCollectionSummary(
        spectrum_count=spectrum_count,
        rejected_block_count=len(parse_report.rejected_spectra),
        total_peak_count=total_peak_count,
        average_peak_count=average_peak_count,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        issue_counts=dict(sorted(issue_counts.items())),
    )


def inspect_mzml_decoding_support(path: Path) -> MzmlDecodingSupportReport:
    """Inspect mzML binary arrays and summarize decoding support boundaries."""

    root = ET.parse(path).getroot()
    if root is None:
        raise ValueError("invalid XML: missing document root")
    compression: set[str] = set()
    precision: set[str] = set()
    for param in root.findall(".//{*}cvParam"):
        accession = param.attrib.get("accession", "").strip()
        if not accession:
            continue
        if accession in {
            _CV_ZLIB,
            _CV_NO_COMPRESSION,
            _CV_NUMPRESS_LINEAR,
            _CV_NUMPRESS_PIC,
            _CV_NUMPRESS_SLOF,
        }:
            compression.add(accession)
        if accession in {
            _CV_FLOAT32,
            _CV_FLOAT64,
            _CV_INT32,
            _CV_INT64,
        }:
            precision.add(accession)

    parse_report = parse_mzml(path)
    issue_codes = {
        issue.code
        for rejected in parse_report.rejected_spectra
        for issue in rejected.issues
    }
    supported = not issue_codes.intersection(
        {"unsupported_binary_compression", "unsupported_binary_precision"}
    )
    diagnostics: tuple[str, ...] = (
        "mzML decoding supports zlib/no-compression float arrays",
        "unsupported compression or precision is reported with explicit issue codes",
    )
    if not supported:
        diagnostics = (
            *diagnostics,
            "this file includes unsupported binary decoding settings for current ingestion boundaries",
        )
    return MzmlDecodingSupportReport(
        supported=supported,
        spectrum_count=parse_report.total_spectra,
        accepted_spectrum_count=len(parse_report.accepted_spectra),
        rejected_spectrum_count=len(parse_report.rejected_spectra),
        compression_accessions=tuple(sorted(compression)),
        precision_accessions=tuple(sorted(precision)),
        diagnostics=diagnostics,
    )


def build_mzml_practical_review_report(path: Path) -> MzmlPracticalReviewReport:
    """Build a practical mzML review surface without overclaiming vendor parity."""

    parse_report = parse_mzml(path)
    decoding_support = inspect_mzml_decoding_support(path)
    chromatograms = extract_mzml_chromatograms(path)
    summary = build_mzml_collection_summary(parse_report).to_dict()
    diagnostics = [
        "mzML review preserves accepted spectra, rejected spectra, and run metadata",
        "binary-array decoding support is reported explicitly rather than assumed from file suffix alone",
    ]
    if chromatograms.total_chromatograms:
        diagnostics.append(
            "chromatogram traces preserve TIC/BPC arrays when present in the mzML run"
        )
    else:
        diagnostics.append(
            "no chromatogram traces were present in the mzML run; TIC/BPC support remains absent rather than guessed"
        )
    return MzmlPracticalReviewReport(
        metadata=parse_report.metadata,
        summary=summary,
        decoding_support=decoding_support,
        chromatograms=chromatograms,
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "MzmlChromatogramPoint",
    "MzmlChromatogramReport",
    "MzmlChromatogramTrace",
    "MzmlDecodingSupportReport",
    "MzmlParseReport",
    "MzmlPracticalReviewReport",
    "MzmlRunMetadata",
    "RejectedMzmlChromatogram",
    "RejectedMzmlSpectrum",
    "build_mzml_collection_summary",
    "build_mzml_practical_review_report",
    "extract_mzml_chromatograms",
    "extract_mzml_metadata",
    "inspect_mzml_decoding_support",
    "parse_mzml",
    "stream_mzml_spectra",
]
