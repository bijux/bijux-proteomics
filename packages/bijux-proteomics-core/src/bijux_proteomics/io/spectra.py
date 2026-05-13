# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum, MGF, and fragment-annotation contracts."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import json
from pathlib import Path
import re
from typing import Iterator

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import (
    FragmentIon,
    ParsedModifiedPeptide,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class SpectrumPeak(JsonModel):
    """One centroided spectrum peak."""

    model_config = ConfigDict(extra="forbid")

    mz: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)


class SpectrumModel(JsonModel):
    """Stable MS/MS spectrum contract."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    native_id: str | None = None
    scan_number: int | None = Field(default=None, ge=1)
    ms_level: int | None = Field(default=None, ge=1)
    parent_spectrum_id: str | None = None
    product_isolation_mz: float | None = Field(default=None, gt=0.0)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int | None = Field(default=None, ge=1)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    peaks: tuple[SpectrumPeak, ...] = Field(default_factory=tuple)
    title: str | None = None

    @field_validator("spectrum_id", mode="before")
    @classmethod
    def _strip_spectrum_id(cls, value: object) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("spectrum_id must not be blank")
        return text


class SpectrumValidationIssue(JsonModel):
    """One parser or spectrum-validation issue."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    block_index: int = Field(..., ge=1)
    field: str | None = None
    line_number: int | None = Field(default=None, ge=1)
    raw_line: str | None = None


class RejectedSpectrumBlock(JsonModel):
    """One rejected MGF block plus stable issues."""

    model_config = ConfigDict(extra="forbid")

    block_index: int = Field(..., ge=1)
    title: str | None = None
    issues: tuple[SpectrumValidationIssue, ...] = Field(default_factory=tuple)
    raw_block: str = ""


class MgfParseReport(JsonModel):
    """Result of parsing one MGF document."""

    model_config = ConfigDict(extra="forbid")

    total_blocks: int = Field(..., ge=0)
    accepted_spectra: tuple[SpectrumModel, ...] = Field(default_factory=tuple)
    rejected_blocks: tuple[RejectedSpectrumBlock, ...] = Field(default_factory=tuple)


class SpectrumCollectionSummary(JsonModel):
    """Compact summary over one parsed MGF collection."""

    model_config = ConfigDict(extra="forbid")

    spectrum_count: int = Field(..., ge=0)
    rejected_block_count: int = Field(..., ge=0)
    total_peak_count: int = Field(..., ge=0)
    average_peak_count: float = Field(..., ge=0.0)
    counts_by_charge: dict[str, int] = Field(default_factory=dict)
    issue_counts: dict[str, int] = Field(default_factory=dict)


class SpectrumLookupIndex(JsonModel):
    """Stable lookup index over parsed spectra."""

    model_config = ConfigDict(extra="forbid")

    spectra: tuple[SpectrumModel, ...] = Field(default_factory=tuple)
    native_id_index: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    title_index: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    scan_number_index: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    scan_key_index: dict[str, tuple[str, ...]] = Field(default_factory=dict)


class SpectralSimilarityMethod(StrEnum):
    """Supported basic spectral similarity methods."""

    COSINE = "cosine"
    DOT_PRODUCT = "dot_product"


class SpectrumSimilarityMode(StrEnum):
    """Supported deterministic preprocessing modes for spectral comparison."""

    RAW = "raw"
    NORMALIZED = "normalized"
    TOP_N = "top_n"
    TRANSFORMED = "transformed"


class SpectralSimilarityScore(JsonModel):
    """Basic spectral similarity score for two spectra."""

    model_config = ConfigDict(extra="forbid")

    method: SpectralSimilarityMethod
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW
    tolerance_da: float = Field(..., gt=0.0)
    score: float = Field(..., ge=0.0)
    matched_peak_count: int = Field(..., ge=0)
    reference_peak_count: int = Field(..., ge=0)
    query_peak_count: int = Field(..., ge=0)


class SpectrumProvenanceManifest(JsonModel):
    """Stable provenance manifest for a parsed spectrum collection."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_path: str
    source_sha256: str
    format: str = Field(default="mgf", frozen=True)
    total_blocks: int = Field(..., ge=0)
    accepted_spectra: int = Field(..., ge=0)
    rejected_blocks: int = Field(..., ge=0)
    issue_counts: dict[str, int] = Field(default_factory=dict)


class PeakNormalizationPolicy(JsonModel):
    """Stable peak-normalization policy."""

    model_config = ConfigDict(extra="forbid")

    merge_tolerance_da: float = Field(default=0.0, ge=0.0)
    drop_zero_intensity: bool = True
    scale_to_base_peak: bool = False


class SpectrumFilterReport(JsonModel):
    """Result of applying stable spectrum peak filters."""

    model_config = ConfigDict(extra="forbid")

    input_peak_count: int = Field(..., ge=0)
    output_peak_count: int = Field(..., ge=0)
    removed_by_mz_window: int = Field(..., ge=0)
    removed_by_intensity: int = Field(..., ge=0)
    removed_by_rank: int = Field(..., ge=0)
    spectrum: SpectrumModel


class SpectrumMetrics(JsonModel):
    """Basic TIC and base-peak metrics for one spectrum."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peak_count: int = Field(..., ge=0)
    total_ion_current: float = Field(..., ge=0.0)
    base_peak_mz: float | None = Field(default=None, gt=0.0)
    base_peak_intensity: float | None = Field(default=None, ge=0.0)
    mz_min: float | None = Field(default=None, gt=0.0)
    mz_max: float | None = Field(default=None, gt=0.0)


class PrecursorMassError(JsonModel):
    """Precursor mass error in Dalton and ppm."""

    model_config = ConfigDict(extra="forbid")

    observed_mz: float = Field(..., gt=0.0)
    theoretical_mz: float = Field(..., gt=0.0)
    delta_da: float
    delta_ppm: float


class PrecursorIsotopeOffsetCandidate(JsonModel):
    """One candidate precursor isotope offset interpretation."""

    model_config = ConfigDict(extra="forbid")

    isotope_offset: int = Field(..., ge=0)
    expected_mz: float = Field(..., gt=0.0)
    delta_da: float
    delta_ppm: float


class PrecursorIsotopeOffsetAdvisory(JsonModel):
    """Advisory-only precursor isotope offset assessment."""

    model_config = ConfigDict(extra="forbid")

    advisory_only: bool = True
    recommended_offset: int = Field(..., ge=0)
    candidates: tuple[PrecursorIsotopeOffsetCandidate, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class SpectrumAnnotationMatch(JsonModel):
    """One theoretical fragment matched to one observed peak."""

    model_config = ConfigDict(extra="forbid")

    fragment: FragmentIon
    fragment_label: str = Field(..., min_length=1)
    observed_mz: float = Field(..., gt=0.0)
    observed_intensity: float = Field(..., ge=0.0)
    mass_error_da: float
    mass_error_ppm: float


class SpectrumAnnotationAmbiguityKind(StrEnum):
    """Supported ambiguity warnings for spectrum annotation."""

    PEAK_TO_MULTIPLE_FRAGMENTS = "peak_to_multiple_fragments"
    FRAGMENT_TO_MULTIPLE_PEAKS = "fragment_to_multiple_peaks"


class SpectrumAnnotationAmbiguityWarning(JsonModel):
    """One ambiguity warning caused by a permissive annotation tolerance."""

    model_config = ConfigDict(extra="forbid")

    kind: SpectrumAnnotationAmbiguityKind
    fragment_labels: tuple[str, ...] = Field(default_factory=tuple)
    peak_mzs: tuple[float, ...] = Field(default_factory=tuple)
    tolerance_da: float = Field(..., gt=0.0)
    note: str = Field(..., min_length=1)


class SpectrumAnnotation(JsonModel):
    """Stable annotation output for one spectrum and peptide."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int | None = Field(default=None, ge=1)
    tolerance_da: float = Field(..., gt=0.0)
    matches: tuple[SpectrumAnnotationMatch, ...] = Field(default_factory=tuple)
    ambiguity_warnings: tuple[SpectrumAnnotationAmbiguityWarning, ...] = Field(
        default_factory=tuple
    )
    unmatched_peak_count: int = Field(..., ge=0)


class SpectrumPlotPeak(JsonModel):
    """Plot-ready peak point with optional annotation labels."""

    model_config = ConfigDict(extra="forbid")

    mz: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)
    labels: tuple[str, ...] = Field(default_factory=tuple)


class SpectrumPlotPayload(JsonModel):
    """Stable JSON plot payload for docs or UI rendering."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    spectrum_id: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int | None = Field(default=None, ge=1)
    peaks: tuple[SpectrumPlotPeak, ...] = Field(default_factory=tuple)


class SpectrumAnnotationParameters(JsonModel):
    """Stable parameter set for one spectrum-annotation bundle."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    tolerance_da: float = Field(..., gt=0.0)
    include_neutral_losses: bool


class AnnotatedSpectrumBundle(JsonModel):
    """Single export bundle with raw peaks, annotation, theoretical ions, and parameters."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    spectrum: SpectrumModel
    annotation: SpectrumAnnotation
    theoretical_fragments: tuple[FragmentIon, ...] = Field(default_factory=tuple)
    parameters: SpectrumAnnotationParameters


class _MgfBlock:
    def __init__(self, block_index: int) -> None:
        self.block_index = block_index
        self.title: str | None = None
        self.spectrum_id: str | None = None
        self.precursor_mz: float | None = None
        self.precursor_charge: int | None = None
        self.retention_time_seconds: float | None = None
        self.peaks: list[SpectrumPeak] = []
        self.issues: list[SpectrumValidationIssue] = []
        self.raw_lines: list[str] = []


class _ParsedMgfBlockResult:
    def __init__(
        self,
        *,
        block_index: int,
        accepted_spectrum: SpectrumModel | None = None,
        rejected_block: RejectedSpectrumBlock | None = None,
    ) -> None:
        self.block_index = block_index
        self.accepted_spectrum = accepted_spectrum
        self.rejected_block = rejected_block


def _scan_number_from_text(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.search(r"scan=(\d+)", value, flags=re.IGNORECASE)
    if match is not None:
        return int(match.group(1))
    if value.isdigit():
        return int(value)
    return None


def normalize_spectrum_scan_key(
    spectrum_or_text: SpectrumModel | str | None,
) -> str | None:
    """Normalize one scan-like identifier onto a stable key."""
    if spectrum_or_text is None:
        return None
    if isinstance(spectrum_or_text, SpectrumModel):
        candidates = (
            spectrum_or_text.native_id,
            spectrum_or_text.spectrum_id,
            spectrum_or_text.title,
        )
        scan_number = spectrum_or_text.scan_number
        if scan_number is not None:
            return f"scan:{scan_number}"
        for candidate in candidates:
            parsed = _scan_number_from_text(candidate)
            if parsed is not None:
                return f"scan:{parsed}"
        return None
    parsed = _scan_number_from_text(spectrum_or_text)
    if parsed is not None:
        return f"scan:{parsed}"
    return None


def _issue(
    block_index: int,
    code: str,
    message: str,
    *,
    field: str | None = None,
    line_number: int | None = None,
    raw_line: str | None = None,
) -> SpectrumValidationIssue:
    return SpectrumValidationIssue(
        code=code,
        message=message,
        block_index=block_index,
        field=field,
        line_number=line_number,
        raw_line=raw_line,
    )


def _parse_charge(token: str) -> int:
    normalized = token.strip()
    if not normalized:
        raise ValueError("empty charge token")
    matches = re.findall(r"[+-]?\d+\+*", normalized.replace("and", ","))
    if not matches:
        raise ValueError("invalid charge token")
    charges = {
        int(match.lstrip("+").rstrip("+"))
        for match in matches
        if match.lstrip("+").rstrip("+")
    }
    if not charges:
        raise ValueError("invalid charge token")
    if len(charges) > 1:
        raise ValueError("ambiguous precursor charge list")
    return next(iter(charges))


def _append_mgf_metadata_issue(
    block: _MgfBlock,
    *,
    key: str,
    raw_line: str,
    line_number: int,
    error: ValueError,
) -> None:
    block.issues.append(
        _issue(
            block.block_index,
            f"invalid_{key.lower()}",
            str(error),
            field=key,
            line_number=line_number,
            raw_line=raw_line,
        )
    )


def _parse_mgf_metadata_line(
    block: _MgfBlock,
    *,
    key: str,
    value: str,
    raw_line: str,
    line_number: int,
) -> None:
    try:
        if key == "TITLE":
            block.title = value
            if block.spectrum_id is None:
                block.spectrum_id = value
        elif key in {"SCANS", "SPECTRUMID"}:
            block.spectrum_id = value
        elif key == "PEPMASS":
            block.precursor_mz = float(value.split()[0])
        elif key == "CHARGE":
            block.precursor_charge = _parse_charge(value)
        elif key == "RTINSECONDS":
            block.retention_time_seconds = float(value)
        elif key == "RTINMINUTES":
            block.retention_time_seconds = float(value) * 60.0
    except ValueError as exc:
        _append_mgf_metadata_issue(
            block,
            key=key,
            raw_line=raw_line,
            line_number=line_number,
            error=exc,
        )


def _finalize_mgf_block(block: _MgfBlock) -> _ParsedMgfBlockResult:
    if block.precursor_mz is None:
        block.issues.append(
            _issue(block.block_index, "missing_precursor_mz", "PEPMASS is required")
        )
    if not block.peaks:
        block.issues.append(
            _issue(block.block_index, "missing_peaks", "at least one peak is required")
        )
    spectrum_id = block.spectrum_id or block.title or f"spectrum-{block.block_index}"
    if block.issues:
        return _ParsedMgfBlockResult(
            block_index=block.block_index,
            rejected_block=RejectedSpectrumBlock(
                block_index=block.block_index,
                title=block.title,
                issues=tuple(block.issues),
                raw_block="\n".join(block.raw_lines),
            ),
        )
    return _ParsedMgfBlockResult(
        block_index=block.block_index,
        accepted_spectrum=SpectrumModel(
            spectrum_id=spectrum_id,
            native_id=block.spectrum_id,
            scan_number=_scan_number_from_text(block.spectrum_id or block.title),
            precursor_mz=block.precursor_mz or 1.0,
            precursor_charge=block.precursor_charge,
            retention_time_seconds=block.retention_time_seconds,
            peaks=tuple(block.peaks),
            title=block.title,
        ),
    )


def _iterate_mgf_parse_results(path: Path) -> Iterator[_ParsedMgfBlockResult]:
    current: _MgfBlock | None = None
    block_index = 0

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped_line = raw_line.rstrip("\n")
            line = stripped_line.strip()
            if not line or line.startswith(("#", ";", "!", "//")):
                continue
            if line.upper() == "BEGIN IONS":
                if current is not None:
                    current.issues.append(
                        _issue(
                            current.block_index,
                            "missing_end_ions",
                            "missing END IONS before next block",
                            line_number=line_number,
                            raw_line=stripped_line,
                        )
                    )
                    yield _finalize_mgf_block(current)
                block_index += 1
                current = _MgfBlock(block_index)
                current.raw_lines.append(stripped_line)
                continue
            if current is None:
                continue
            current.raw_lines.append(stripped_line)
            if line.upper() == "END IONS":
                yield _finalize_mgf_block(current)
                current = None
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                _parse_mgf_metadata_line(
                    current,
                    key=key.strip().upper(),
                    value=value.strip(),
                    raw_line=stripped_line,
                    line_number=line_number,
                )
                continue
            tokens = line.split()
            if len(tokens) != 2:
                current.issues.append(
                    _issue(
                        current.block_index,
                        "invalid_peak_line",
                        f"invalid peak line {line!r}",
                        field="PEAK",
                        line_number=line_number,
                        raw_line=stripped_line,
                    )
                )
                continue
            try:
                peak = SpectrumPeak(mz=float(tokens[0]), intensity=float(tokens[1]))
            except ValueError as exc:
                current.issues.append(
                    _issue(
                        current.block_index,
                        "invalid_peak_value",
                        str(exc),
                        field="PEAK",
                        line_number=line_number,
                        raw_line=stripped_line,
                    )
                )
                continue
            current.peaks.append(peak)

    if current is not None:
        current.issues.append(
            _issue(
                current.block_index, "missing_end_ions", "unterminated spectrum block"
            )
        )
        yield _finalize_mgf_block(current)


def iter_mgf_spectra(path: Path) -> Iterator[SpectrumModel]:
    """Yield accepted MGF spectra one block at a time from a streaming parse."""
    for result in _iterate_mgf_parse_results(path):
        if result.accepted_spectrum is not None:
            yield result.accepted_spectrum


def parse_mgf(path: Path) -> MgfParseReport:
    """Parse an MGF file into stable spectrum contracts through streaming IO."""
    accepted: list[SpectrumModel] = []
    rejected: list[RejectedSpectrumBlock] = []
    total_blocks = 0

    for result in _iterate_mgf_parse_results(path):
        total_blocks = result.block_index
        if result.accepted_spectrum is not None:
            accepted.append(result.accepted_spectrum)
        elif result.rejected_block is not None:
            rejected.append(result.rejected_block)

    return MgfParseReport(
        total_blocks=total_blocks,
        accepted_spectra=tuple(accepted),
        rejected_blocks=tuple(rejected),
    )


def build_spectrum_collection_summary(
    parse_report: MgfParseReport,
) -> SpectrumCollectionSummary:
    """Build a compact summary for one parsed spectrum collection."""
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
    for block in parse_report.rejected_blocks:
        for issue in block.issues:
            issue_counts[issue.code] = issue_counts.get(issue.code, 0) + 1
    spectrum_count = len(parse_report.accepted_spectra)
    return SpectrumCollectionSummary(
        spectrum_count=spectrum_count,
        rejected_block_count=len(parse_report.rejected_blocks),
        total_peak_count=total_peak_count,
        average_peak_count=(total_peak_count / spectrum_count)
        if spectrum_count
        else 0.0,
        counts_by_charge=dict(sorted(counts_by_charge.items())),
        issue_counts=dict(sorted(issue_counts.items())),
    )


def build_spectrum_lookup_index(
    spectra: tuple[SpectrumModel, ...],
) -> SpectrumLookupIndex:
    """Build stable lookup maps by native ID, title, scan number, and scan key."""
    native_id_index: dict[str, list[str]] = {}
    title_index: dict[str, list[str]] = {}
    scan_number_index: dict[str, list[str]] = {}
    scan_key_index: dict[str, list[str]] = {}
    normalized_spectra = tuple(sorted(spectra, key=lambda item: item.spectrum_id))
    for spectrum in normalized_spectra:
        if spectrum.native_id:
            native_id_index.setdefault(spectrum.native_id, []).append(
                spectrum.spectrum_id
            )
        if spectrum.title:
            title_index.setdefault(spectrum.title, []).append(spectrum.spectrum_id)
        if spectrum.scan_number is not None:
            scan_number_index.setdefault(str(spectrum.scan_number), []).append(
                spectrum.spectrum_id
            )
        scan_key = normalize_spectrum_scan_key(spectrum)
        if scan_key is not None:
            scan_key_index.setdefault(scan_key, []).append(spectrum.spectrum_id)
    return SpectrumLookupIndex(
        spectra=normalized_spectra,
        native_id_index={
            key: tuple(values) for key, values in sorted(native_id_index.items())
        },
        title_index={key: tuple(values) for key, values in sorted(title_index.items())},
        scan_number_index={
            key: tuple(values) for key, values in sorted(scan_number_index.items())
        },
        scan_key_index={
            key: tuple(values) for key, values in sorted(scan_key_index.items())
        },
    )


def lookup_spectra(
    index: SpectrumLookupIndex,
    *,
    native_id: str | None = None,
    title: str | None = None,
    scan_number: int | None = None,
    scan_key: str | None = None,
) -> tuple[SpectrumModel, ...]:
    """Look up spectra by one stable key family."""
    if (
        sum(query is not None for query in (native_id, title, scan_number, scan_key))
        != 1
    ):
        raise ValueError(
            "exactly one of native_id, title, scan_number, or scan_key must be provided"
        )
    if native_id is not None:
        matched_ids = index.native_id_index.get(native_id, ())
    elif title is not None:
        matched_ids = index.title_index.get(title, ())
    elif scan_number is not None:
        matched_ids = index.scan_number_index.get(str(scan_number), ())
    else:
        normalized_key = normalize_spectrum_scan_key(scan_key)
        matched_ids = index.scan_key_index.get(normalized_key or "", ())
    spectra_by_id = {spectrum.spectrum_id: spectrum for spectrum in index.spectra}
    return tuple(spectra_by_id[spectrum_id] for spectrum_id in matched_ids)


def build_spectrum_provenance_manifest(
    *,
    source_path: Path,
    parse_report: MgfParseReport,
) -> SpectrumProvenanceManifest:
    """Build a stable provenance manifest for one MGF parse run."""
    issue_counts = build_spectrum_collection_summary(parse_report).issue_counts
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SpectrumProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        total_blocks=parse_report.total_blocks,
        accepted_spectra=len(parse_report.accepted_spectra),
        rejected_blocks=len(parse_report.rejected_blocks),
        issue_counts=issue_counts,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def render_mgf(spectra: tuple[SpectrumModel, ...]) -> str:
    """Render stable spectrum contracts into MGF text."""
    lines: list[str] = []
    for spectrum in spectra:
        lines.append("BEGIN IONS")
        lines.append(f"TITLE={spectrum.title or spectrum.spectrum_id}")
        if spectrum.title is None or spectrum.title != spectrum.spectrum_id:
            lines.append(f"SCANS={spectrum.spectrum_id}")
        lines.append(f"PEPMASS={spectrum.precursor_mz:.6f}".rstrip("0").rstrip("."))
        if spectrum.precursor_charge is not None:
            lines.append(f"CHARGE={spectrum.precursor_charge}+")
        if spectrum.retention_time_seconds is not None:
            lines.append(
                f"RTINSECONDS={spectrum.retention_time_seconds:.4f}".rstrip("0").rstrip(
                    "."
                )
            )
        for peak in spectrum.peaks:
            lines.append(
                f"{peak.mz:.6f}".rstrip("0").rstrip(".")
                + " "
                + f"{peak.intensity:.6f}".rstrip("0").rstrip(".")
            )
        lines.append("END IONS")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def normalize_spectrum_peaks(
    spectrum: SpectrumModel,
    *,
    policy: PeakNormalizationPolicy | None = None,
) -> SpectrumModel:
    """Sort peaks, merge near-duplicate m/z values, and optionally scale intensity."""
    active_policy = policy or PeakNormalizationPolicy()
    merged: list[SpectrumPeak] = []
    for peak in sorted(spectrum.peaks, key=lambda item: (item.mz, item.intensity)):
        if active_policy.drop_zero_intensity and peak.intensity == 0.0:
            continue
        if merged and abs(merged[-1].mz - peak.mz) <= active_policy.merge_tolerance_da:
            previous = merged[-1]
            weighted_mz = (
                (previous.mz * previous.intensity) + (peak.mz * peak.intensity)
            ) / max(
                previous.intensity + peak.intensity,
                1e-12,
            )
            merged[-1] = SpectrumPeak(
                mz=weighted_mz,
                intensity=previous.intensity + peak.intensity,
            )
        else:
            merged.append(peak)
    if active_policy.scale_to_base_peak and merged:
        base_peak = max(merged, key=lambda item: item.intensity)
        if base_peak.intensity > 0.0:
            merged = [
                SpectrumPeak(mz=peak.mz, intensity=peak.intensity / base_peak.intensity)
                for peak in merged
            ]
    return spectrum.model_copy(
        update={"peaks": tuple(sorted(merged, key=lambda item: item.mz))}
    )


def filter_spectrum_peaks(
    spectrum: SpectrumModel,
    *,
    top_n: int | None = None,
    min_relative_intensity: float | None = None,
    mz_min: float | None = None,
    mz_max: float | None = None,
) -> SpectrumFilterReport:
    """Filter peaks by m/z window, relative intensity, and top-N rank."""
    peaks = list(spectrum.peaks)
    removed_by_mz_window = 0
    removed_by_intensity = 0
    removed_by_rank = 0

    if mz_min is not None or mz_max is not None:
        filtered_window: list[SpectrumPeak] = []
        for peak in peaks:
            if mz_min is not None and peak.mz < mz_min:
                removed_by_mz_window += 1
                continue
            if mz_max is not None and peak.mz > mz_max:
                removed_by_mz_window += 1
                continue
            filtered_window.append(peak)
        peaks = filtered_window

    if min_relative_intensity is not None and peaks:
        base_peak_intensity = max(peak.intensity for peak in peaks)
        threshold = base_peak_intensity * min_relative_intensity
        retained: list[SpectrumPeak] = []
        for peak in peaks:
            if peak.intensity < threshold:
                removed_by_intensity += 1
                continue
            retained.append(peak)
        peaks = retained

    if top_n is not None and top_n >= 0 and len(peaks) > top_n:
        ranked = sorted(peaks, key=lambda item: (-item.intensity, item.mz))
        keep_ids = {(peak.mz, peak.intensity) for peak in ranked[:top_n]}
        retained = []
        for peak in peaks:
            if (peak.mz, peak.intensity) in keep_ids:
                retained.append(peak)
                keep_ids.remove((peak.mz, peak.intensity))
            else:
                removed_by_rank += 1
        peaks = retained

    filtered_spectrum = spectrum.model_copy(
        update={"peaks": tuple(sorted(peaks, key=lambda item: item.mz))}
    )
    return SpectrumFilterReport(
        input_peak_count=len(spectrum.peaks),
        output_peak_count=len(filtered_spectrum.peaks),
        removed_by_mz_window=removed_by_mz_window,
        removed_by_intensity=removed_by_intensity,
        removed_by_rank=removed_by_rank,
        spectrum=filtered_spectrum,
    )


def build_spectrum_metrics(spectrum: SpectrumModel) -> SpectrumMetrics:
    """Compute basic TIC and base-peak metrics."""
    if not spectrum.peaks:
        return SpectrumMetrics(
            spectrum_id=spectrum.spectrum_id,
            peak_count=0,
            total_ion_current=0.0,
        )
    base_peak = max(spectrum.peaks, key=lambda peak: (peak.intensity, -peak.mz))
    return SpectrumMetrics(
        spectrum_id=spectrum.spectrum_id,
        peak_count=len(spectrum.peaks),
        total_ion_current=sum(peak.intensity for peak in spectrum.peaks),
        base_peak_mz=base_peak.mz,
        base_peak_intensity=base_peak.intensity,
        mz_min=min(peak.mz for peak in spectrum.peaks),
        mz_max=max(peak.mz for peak in spectrum.peaks),
    )


def calculate_precursor_mass_error(
    *,
    observed_mz: float,
    theoretical_mz: float,
) -> PrecursorMassError:
    """Calculate precursor mass error in Dalton and ppm."""
    delta_da = observed_mz - theoretical_mz
    delta_ppm = (delta_da / theoretical_mz) * 1_000_000.0
    return PrecursorMassError(
        observed_mz=observed_mz,
        theoretical_mz=theoretical_mz,
        delta_da=delta_da,
        delta_ppm=delta_ppm,
    )


def detect_precursor_isotope_offset_advisory(
    *,
    observed_mz: float,
    theoretical_mz: float,
    charge: int,
    max_offset: int = 3,
) -> PrecursorIsotopeOffsetAdvisory:
    """Rank precursor isotope offset candidates without enforcing any correction."""
    isotope_delta = 1.0033548378 / charge
    candidates = tuple(
        PrecursorIsotopeOffsetCandidate(
            isotope_offset=offset,
            expected_mz=theoretical_mz + (isotope_delta * offset),
            delta_da=observed_mz - (theoretical_mz + (isotope_delta * offset)),
            delta_ppm=(
                (observed_mz - (theoretical_mz + (isotope_delta * offset)))
                / (theoretical_mz + (isotope_delta * offset))
            )
            * 1_000_000.0,
        )
        for offset in range(max_offset + 1)
    )
    ranked = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                abs(candidate.delta_da),
                candidate.isotope_offset,
            ),
        )
    )
    best = ranked[0]
    note = (
        "observed precursor is closest to the monoisotopic assignment"
        if best.isotope_offset == 0
        else f"observed precursor is closest to isotope offset +{best.isotope_offset}"
    )
    return PrecursorIsotopeOffsetAdvisory(
        advisory_only=True,
        recommended_offset=best.isotope_offset,
        candidates=ranked,
        note=note,
    )


def calculate_spectral_similarity(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float = 0.02,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
) -> SpectralSimilarityScore:
    """Calculate a basic matched-peak spectral similarity score."""
    reference_spectrum = _prepare_similarity_spectrum(
        reference_spectrum,
        mode=mode,
        top_n=top_n,
    )
    query_spectrum = _prepare_similarity_spectrum(
        query_spectrum,
        mode=mode,
        top_n=top_n,
    )
    matched_reference: list[float] = []
    matched_query: list[float] = []
    used_reference_indices: set[int] = set()
    for query_peak in sorted(query_spectrum.peaks, key=lambda peak: peak.mz):
        best_index: int | None = None
        best_error: float | None = None
        for index, reference_peak in enumerate(reference_spectrum.peaks):
            if index in used_reference_indices:
                continue
            error = query_peak.mz - reference_peak.mz
            if abs(error) > tolerance_da:
                continue
            if best_index is None or best_error is None or abs(error) < abs(best_error):
                best_index = index
                best_error = error
        if best_index is None:
            continue
        used_reference_indices.add(best_index)
        matched_reference.append(reference_spectrum.peaks[best_index].intensity)
        matched_query.append(query_peak.intensity)

    dot_product = sum(
        reference * query
        for reference, query in zip(matched_reference, matched_query, strict=True)
    )
    if method is SpectralSimilarityMethod.DOT_PRODUCT:
        score = dot_product
    else:
        reference_norm = sum(value * value for value in matched_reference) ** 0.5
        query_norm = sum(value * value for value in matched_query) ** 0.5
        score = (
            0.0
            if reference_norm == 0.0 or query_norm == 0.0
            else dot_product / (reference_norm * query_norm)
        )
    return SpectralSimilarityScore(
        method=method,
        mode=mode,
        tolerance_da=tolerance_da,
        score=score,
        matched_peak_count=len(matched_reference),
        reference_peak_count=len(reference_spectrum.peaks),
        query_peak_count=len(query_spectrum.peaks),
    )


def _prepare_similarity_spectrum(
    spectrum: SpectrumModel,
    *,
    mode: SpectrumSimilarityMode,
    top_n: int | None,
) -> SpectrumModel:
    if mode is SpectrumSimilarityMode.RAW:
        return normalize_spectrum_peaks(
            spectrum,
            policy=PeakNormalizationPolicy(
                merge_tolerance_da=0.0,
                drop_zero_intensity=False,
                scale_to_base_peak=False,
            ),
        )
    if mode is SpectrumSimilarityMode.NORMALIZED:
        return normalize_spectrum_peaks(
            spectrum,
            policy=PeakNormalizationPolicy(
                merge_tolerance_da=0.0,
                drop_zero_intensity=False,
                scale_to_base_peak=True,
            ),
        )
    if mode is SpectrumSimilarityMode.TOP_N:
        normalized = normalize_spectrum_peaks(
            spectrum,
            policy=PeakNormalizationPolicy(
                merge_tolerance_da=0.0,
                drop_zero_intensity=False,
                scale_to_base_peak=True,
            ),
        )
        return filter_spectrum_peaks(
            normalized,
            top_n=top_n if top_n is not None else 50,
        ).spectrum
    normalized = normalize_spectrum_peaks(
        spectrum,
        policy=PeakNormalizationPolicy(
            merge_tolerance_da=0.0,
            drop_zero_intensity=False,
            scale_to_base_peak=True,
        ),
    )
    return normalized.model_copy(
        update={
            "peaks": tuple(
                SpectrumPeak(mz=peak.mz, intensity=peak.intensity**0.5)
                for peak in normalized.peaks
            )
        }
    )


def _canonical_peptide_text(peptide: str | ParsedModifiedPeptide) -> str:
    if isinstance(peptide, ParsedModifiedPeptide):
        return canonicalize_modified_peptide(peptide)
    return canonicalize_modified_peptide(peptide)


def _fragment_label(fragment: FragmentIon) -> str:
    return f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}"


def annotate_spectrum_fragments(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    tolerance_da: float = 0.5,
    include_neutral_losses: bool = True,
) -> SpectrumAnnotation:
    """Match theoretical fragments against observed peaks within a Dalton tolerance."""
    canonical = _canonical_peptide_text(peptide)
    fragments = calculate_fragment_ions(
        peptide,
        include_neutral_losses=include_neutral_losses,
    )
    matches: list[SpectrumAnnotationMatch] = []
    ambiguity_warnings: list[SpectrumAnnotationAmbiguityWarning] = []
    matched_peak_keys: set[tuple[float, float]] = set()
    candidate_fragments_by_peak: dict[tuple[float, float], list[str]] = {}
    for fragment in fragments:
        candidate_peaks = tuple(
            peak
            for peak in spectrum.peaks
            if abs(peak.mz - fragment.mz_monoisotopic) <= tolerance_da
        )
        fragment_label = _fragment_label(fragment)
        if len(candidate_peaks) > 1:
            ambiguity_warnings.append(
                SpectrumAnnotationAmbiguityWarning(
                    kind=SpectrumAnnotationAmbiguityKind.FRAGMENT_TO_MULTIPLE_PEAKS,
                    fragment_labels=(fragment_label,),
                    peak_mzs=tuple(sorted(peak.mz for peak in candidate_peaks)),
                    tolerance_da=tolerance_da,
                    note="one fragment is compatible with multiple observed peaks under the requested tolerance",
                )
            )
        for peak in candidate_peaks:
            candidate_fragments_by_peak.setdefault(
                (peak.mz, peak.intensity), []
            ).append(fragment_label)
        best_peak: SpectrumPeak | None = None
        best_error: float | None = None
        for peak in spectrum.peaks:
            error = peak.mz - fragment.mz_monoisotopic
            if abs(error) > tolerance_da:
                continue
            if (
                best_peak is None
                or best_error is None
                or abs(error) < abs(best_error)
                or (
                    abs(error) == abs(best_error)
                    and peak.intensity > best_peak.intensity
                )
            ):
                best_peak = peak
                best_error = error
        if best_peak is None or best_error is None:
            continue
        matched_peak_keys.add((best_peak.mz, best_peak.intensity))
        matches.append(
            SpectrumAnnotationMatch(
                fragment=fragment,
                fragment_label=fragment_label,
                observed_mz=best_peak.mz,
                observed_intensity=best_peak.intensity,
                mass_error_da=best_error,
                mass_error_ppm=(best_error / fragment.mz_monoisotopic) * 1_000_000.0,
            )
        )
    for peak_key, fragment_labels in sorted(
        candidate_fragments_by_peak.items(),
        key=lambda item: (item[0][0], item[0][1]),
    ):
        unique_labels = tuple(sorted(set(fragment_labels)))
        if len(unique_labels) < 2:
            continue
        ambiguity_warnings.append(
            SpectrumAnnotationAmbiguityWarning(
                kind=SpectrumAnnotationAmbiguityKind.PEAK_TO_MULTIPLE_FRAGMENTS,
                fragment_labels=unique_labels,
                peak_mzs=(peak_key[0],),
                tolerance_da=tolerance_da,
                note="one observed peak is compatible with multiple theoretical fragments under the requested tolerance",
            )
        )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_annotation",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    annotation = SpectrumAnnotation(
        document_schema=schema,
        spectrum_id=spectrum.spectrum_id,
        peptide=canonical,
        precursor_mz=spectrum.precursor_mz,
        precursor_charge=spectrum.precursor_charge,
        tolerance_da=tolerance_da,
        matches=tuple(
            sorted(
                matches,
                key=lambda match: (
                    match.fragment.series.value,
                    match.fragment.ordinal,
                    match.fragment.charge,
                ),
            )
        ),
        ambiguity_warnings=tuple(
            sorted(
                ambiguity_warnings,
                key=lambda warning: (
                    warning.kind.value,
                    warning.fragment_labels,
                    warning.peak_mzs,
                ),
            )
        ),
        unmatched_peak_count=sum(
            1
            for peak in spectrum.peaks
            if (peak.mz, peak.intensity) not in matched_peak_keys
        ),
    )
    payload = annotation.to_dict()
    return annotation.model_copy(
        update={
            "document_schema": annotation.document_schema.with_content_hash(payload)
        }
    )


def export_spectrum_annotation_tsv(annotation: SpectrumAnnotation, path: Path) -> None:
    """Write a stable TSV table for one spectrum annotation."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "spectrum_id",
                "peptide",
                "series",
                "ordinal",
                "fragment_charge",
                "fragment_mz",
                "observed_mz",
                "observed_intensity",
                "mass_error_da",
                "mass_error_ppm",
                "label",
            ]
        )
        for match in annotation.matches:
            writer.writerow(
                [
                    annotation.spectrum_id,
                    annotation.peptide,
                    match.fragment.series.value,
                    match.fragment.ordinal,
                    match.fragment.charge,
                    match.fragment.mz_monoisotopic,
                    match.observed_mz,
                    match.observed_intensity,
                    match.mass_error_da,
                    match.mass_error_ppm,
                    match.fragment_label,
                ]
            )


def build_spectrum_plot_payload(
    spectrum: SpectrumModel,
    *,
    annotation: SpectrumAnnotation | None = None,
) -> SpectrumPlotPayload:
    """Build a stable JSON payload consumable by docs or a UI plot layer."""
    labels_by_peak: dict[tuple[float, float], list[str]] = {}
    if annotation is not None:
        for match in annotation.matches:
            labels_by_peak.setdefault(
                (match.observed_mz, match.observed_intensity), []
            ).append(match.fragment_label)
    peaks = tuple(
        SpectrumPlotPeak(
            mz=peak.mz,
            intensity=peak.intensity,
            labels=tuple(sorted(labels_by_peak.get((peak.mz, peak.intensity), ()))),
        )
        for peak in spectrum.peaks
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_plot_payload",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    payload = SpectrumPlotPayload(
        document_schema=schema,
        spectrum_id=spectrum.spectrum_id,
        precursor_mz=spectrum.precursor_mz,
        precursor_charge=spectrum.precursor_charge,
        peaks=peaks,
    )
    return payload.model_copy(
        update={
            "document_schema": payload.document_schema.with_content_hash(
                payload.to_dict()
            )
        }
    )


def build_annotated_spectrum_bundle(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    tolerance_da: float = 0.5,
    include_neutral_losses: bool = True,
) -> AnnotatedSpectrumBundle:
    """Build one self-contained annotation bundle with raw and theoretical evidence."""
    canonical = _canonical_peptide_text(peptide)
    theoretical_fragments = calculate_fragment_ions(
        peptide,
        include_neutral_losses=include_neutral_losses,
    )
    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide=peptide,
        tolerance_da=tolerance_da,
        include_neutral_losses=include_neutral_losses,
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="annotated_spectrum_bundle",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    bundle = AnnotatedSpectrumBundle(
        document_schema=schema,
        spectrum=spectrum,
        annotation=annotation,
        theoretical_fragments=theoretical_fragments,
        parameters=SpectrumAnnotationParameters(
            peptide=canonical,
            tolerance_da=tolerance_da,
            include_neutral_losses=include_neutral_losses,
        ),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )


def export_annotated_spectrum_bundle(
    bundle: AnnotatedSpectrumBundle,
    path: Path,
) -> None:
    """Write one annotated spectrum bundle as stable JSON."""
    path.write_text(
        json.dumps(bundle.to_dict(), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
