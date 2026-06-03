# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum, MGF, and fragment-annotation contracts."""

from __future__ import annotations

from collections.abc import Iterator
import csv
from enum import StrEnum
import hashlib
import io
import json
from pathlib import Path
import re
from typing import cast

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry import (
    FragmentIon,
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    calculate_fragment_ions,
    calculate_peptide_mz,
    canonicalize_modified_peptide,
)
from bijux_proteomics.io.spectra.spectrum_peak_matching import (
    build_spectrum_peak_match_report,
)
from bijux_proteomics.io.raw.mgf_streaming import (
    iter_mgf_spectra as _iter_mgf_spectra,
    parse_mgf as _parse_mgf,
)
from bijux_proteomics.domain.records import SpectrumRecord as CanonicalSpectrumRecord
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
    isolation_window_target_mz: float | None = Field(default=None, gt=0.0)
    isolation_window_lower_offset: float | None = Field(default=None, ge=0.0)
    isolation_window_upper_offset: float | None = Field(default=None, ge=0.0)
    product_isolation_mz: float | None = Field(default=None, gt=0.0)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_intensity: float | None = Field(default=None, ge=0.0)
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

    def to_domain_record(self) -> CanonicalSpectrumRecord:
        """Convert one parsed spectrum into the canonical domain record."""

        return CanonicalSpectrumRecord(
            spectrum_id=self.spectrum_id,
            precursor_mz=self.precursor_mz,
            peak_count=len(self.peaks),
            native_id=self.native_id,
            ms_level=self.ms_level,
            precursor_charge=self.precursor_charge,
            retention_time_seconds=self.retention_time_seconds,
            precursor_intensity=self.precursor_intensity,
            metadata={
                "source_contract": "io.spectrum_model",
                "title": self.title or "",
                "parent_spectrum_id": self.parent_spectrum_id or "",
                "isolation_window_target_mz": (
                    ""
                    if self.isolation_window_target_mz is None
                    else str(self.isolation_window_target_mz)
                ),
                "isolation_window_lower_offset": (
                    ""
                    if self.isolation_window_lower_offset is None
                    else str(self.isolation_window_lower_offset)
                ),
                "isolation_window_upper_offset": (
                    ""
                    if self.isolation_window_upper_offset is None
                    else str(self.isolation_window_upper_offset)
                ),
            },
        )


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


class SpectrumDistributionRow(JsonModel):
    """One stable distribution bucket for spectrum review."""

    model_config = ConfigDict(extra="forbid")

    bucket: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)


class SpectrumSummaryTableReport(JsonModel):
    """Reviewer-facing spectrum summary tables over one run or collection."""

    model_config = ConfigDict(extra="forbid")

    source_kind: str = Field(..., min_length=1)
    ms_level_policy: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=0)
    rejected_count: int = Field(..., ge=0)
    ms1_spectrum_count: int = Field(..., ge=0)
    ms2_spectrum_count: int = Field(..., ge=0)
    unknown_ms_level_count: int = Field(..., ge=0)
    retention_time_min_seconds: float | None = Field(default=None, ge=0.0)
    retention_time_max_seconds: float | None = Field(default=None, ge=0.0)
    charge_distribution: tuple[SpectrumDistributionRow, ...] = Field(
        default_factory=tuple
    )
    precursor_mz_distribution: tuple[SpectrumDistributionRow, ...] = Field(
        default_factory=tuple
    )
    peak_count_distribution: tuple[SpectrumDistributionRow, ...] = Field(
        default_factory=tuple
    )


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


class SpectrumSimilarityMatchingMode(StrEnum):
    """Supported peak-alignment strategies for spectral comparison."""

    TOLERANCE = "tolerance"
    BINNED = "binned"


class SpectrumSimilarityClassification(StrEnum):
    """Reviewer-facing interpretation classes for one spectral comparison."""

    DUPLICATE_LIKE = "duplicate_like"
    SIMILAR = "similar"
    DISTINCT = "distinct"
    INSUFFICIENT_SIGNAL = "insufficient_signal"


class SpectralSimilarityScore(JsonModel):
    """Basic spectral similarity score for two spectra."""

    model_config = ConfigDict(extra="forbid")

    method: SpectralSimilarityMethod
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW
    matching_mode: SpectrumSimilarityMatchingMode = (
        SpectrumSimilarityMatchingMode.TOLERANCE
    )
    tolerance_da: float | None = Field(default=None, gt=0.0)
    bin_width_da: float | None = Field(default=None, gt=0.0)
    score: float = Field(..., ge=0.0)
    matched_peak_count: int = Field(..., ge=0)
    reference_peak_count: int = Field(..., ge=0)
    query_peak_count: int = Field(..., ge=0)
    reference_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    query_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)


class SpectrumSimilarityParameters(JsonModel):
    """Stable parameter set for one similarity review surface."""

    model_config = ConfigDict(extra="forbid")

    method: SpectralSimilarityMethod
    mode: SpectrumSimilarityMode
    matching_mode: SpectrumSimilarityMatchingMode
    tolerance_da: float | None = Field(default=None, gt=0.0)
    bin_width_da: float | None = Field(default=None, gt=0.0)
    top_n: int | None = Field(default=None, ge=1)


class SpectrumSimilarityComparisonReport(JsonModel):
    """Reviewer-facing similarity comparison between two spectra."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    parameters: SpectrumSimilarityParameters
    reference_spectrum_id: str = Field(..., min_length=1)
    query_spectrum_id: str = Field(..., min_length=1)
    classification: SpectrumSimilarityClassification
    score: float = Field(..., ge=0.0)
    matched_peak_count: int = Field(..., ge=0)
    reference_peak_count: int = Field(..., ge=0)
    query_peak_count: int = Field(..., ge=0)
    reference_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    query_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    interpretation: str = Field(..., min_length=1)


class SpectrumLibrarySimilarityMatch(JsonModel):
    """One ranked library candidate for a query spectrum."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    reference_spectrum_id: str = Field(..., min_length=1)
    classification: SpectrumSimilarityClassification
    score: float = Field(..., ge=0.0)
    matched_peak_count: int = Field(..., ge=0)
    reference_peak_count: int = Field(..., ge=0)
    query_peak_count: int = Field(..., ge=0)
    reference_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    query_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)


class SpectrumLibrarySimilarityReport(JsonModel):
    """Ranked similarity review between one query spectrum and a spectrum library."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    parameters: SpectrumSimilarityParameters
    query_spectrum_id: str = Field(..., min_length=1)
    candidate_count: int = Field(..., ge=0)
    duplicate_like_match_count: int = Field(..., ge=0)
    similar_match_count: int = Field(..., ge=0)
    matches: tuple[SpectrumLibrarySimilarityMatch, ...] = Field(default_factory=tuple)


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


class PrecursorMassErrorQuery(JsonModel):
    """One precursor observation to compare against a theoretical peptide m/z."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    observed_mz: float = Field(..., gt=0.0)
    charge: int = Field(..., ge=1)
    spectrum_id: str | None = None


class PrecursorMassErrorDistributionRow(JsonModel):
    """One stable distribution bucket for precursor mass-error review."""

    model_config = ConfigDict(extra="forbid")

    bucket: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)


class PrecursorMassErrorObservation(JsonModel):
    """One fully interpreted precursor mass-error observation."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    observed_mz: float = Field(..., gt=0.0)
    theoretical_mz: float = Field(..., gt=0.0)
    charge: int = Field(..., ge=1)
    spectrum_id: str | None = None
    delta_da: float
    delta_ppm: float
    absolute_delta_da: float = Field(..., ge=0.0)
    absolute_delta_ppm: float = Field(..., ge=0.0)
    isotope_offset_advisory: PrecursorIsotopeOffsetAdvisory


class PrecursorMassErrorReport(JsonModel):
    """Reviewer-facing precursor mass-error report over one observation set."""

    model_config = ConfigDict(extra="forbid")

    observation_count: int = Field(..., ge=0)
    charge_distribution: tuple[PrecursorMassErrorDistributionRow, ...] = Field(
        default_factory=tuple
    )
    ppm_error_distribution: tuple[PrecursorMassErrorDistributionRow, ...] = Field(
        default_factory=tuple
    )
    isotope_offset_distribution: tuple[PrecursorMassErrorDistributionRow, ...] = Field(
        default_factory=tuple
    )
    mean_delta_ppm: float | None = None
    mean_delta_da: float | None = None
    median_delta_ppm: float | None = None
    median_abs_delta_ppm: float | None = Field(default=None, ge=0.0)
    max_abs_delta_ppm: float | None = Field(default=None, ge=0.0)
    observations: tuple[PrecursorMassErrorObservation, ...] = Field(
        default_factory=tuple
    )


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


class SpectrumAnnotationToleranceUnit(StrEnum):
    """Supported tolerance units for fragment annotation."""

    DA = "da"
    PPM = "ppm"


class SpectrumAnnotationAmbiguityWarning(JsonModel):
    """One ambiguity warning caused by a permissive annotation tolerance."""

    model_config = ConfigDict(extra="forbid")

    kind: SpectrumAnnotationAmbiguityKind
    fragment_labels: tuple[str, ...] = Field(default_factory=tuple)
    peak_mzs: tuple[float, ...] = Field(default_factory=tuple)
    tolerance_unit: SpectrumAnnotationToleranceUnit
    tolerance_da: float | None = Field(default=None, gt=0.0)
    tolerance_ppm: float | None = Field(default=None, gt=0.0)
    note: str = Field(..., min_length=1)


class SpectrumAnnotationUnmatchedPeak(JsonModel):
    """One observed peak that remained unmatched in annotation output."""

    model_config = ConfigDict(extra="forbid")

    mz: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)


class SpectrumAnnotation(JsonModel):
    """Stable annotation output for one spectrum and peptide."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int | None = Field(default=None, ge=1)
    tolerance_unit: SpectrumAnnotationToleranceUnit
    tolerance_da: float | None = Field(default=None, gt=0.0)
    tolerance_ppm: float | None = Field(default=None, gt=0.0)
    matches: tuple[SpectrumAnnotationMatch, ...] = Field(default_factory=tuple)
    unmatched_peaks: tuple[SpectrumAnnotationUnmatchedPeak, ...] = Field(
        default_factory=tuple
    )
    ambiguity_warnings: tuple[SpectrumAnnotationAmbiguityWarning, ...] = Field(
        default_factory=tuple
    )
    matched_peak_count: int = Field(..., ge=0)
    explained_intensity: float = Field(..., ge=0.0)
    total_observed_intensity: float = Field(..., ge=0.0)
    explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
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
    tolerance_unit: SpectrumAnnotationToleranceUnit
    tolerance_da: float | None = Field(default=None, gt=0.0)
    tolerance_ppm: float | None = Field(default=None, gt=0.0)
    include_neutral_losses: bool


class AnnotatedSpectrumBundle(JsonModel):
    """Single export bundle with raw peaks, annotation, theoretical ions, and parameters."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    spectrum: SpectrumModel
    annotation: SpectrumAnnotation
    theoretical_fragments: tuple[FragmentIon, ...] = Field(default_factory=tuple)
    parameters: SpectrumAnnotationParameters


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


def iter_mgf_spectra(path: Path) -> Iterator[SpectrumModel]:
    """Yield accepted MGF spectra one block at a time from a streaming parse."""
    yield from cast(Iterator[SpectrumModel], _iter_mgf_spectra(path))


def parse_mgf(path: Path) -> MgfParseReport:
    """Parse an MGF file into stable spectrum contracts through streaming IO."""
    return cast(MgfParseReport, _parse_mgf(path))


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


def _bucket_count(
    value: int, *, buckets: tuple[tuple[str, int, int | None], ...]
) -> str:
    for label, lower, upper in buckets:
        if value < lower:
            continue
        if upper is None or value <= upper:
            return label
    return buckets[-1][0]


def _bucket_float(
    value: float, *, buckets: tuple[tuple[str, float, float | None], ...]
) -> str:
    for label, lower, upper in buckets:
        if value < lower:
            continue
        if upper is None or value <= upper:
            return label
    return buckets[-1][0]


def build_spectrum_summary_table_report(
    spectra: tuple[SpectrumModel, ...],
    *,
    source_kind: str,
    rejected_count: int = 0,
) -> SpectrumSummaryTableReport:
    """Build reviewer-facing spectrum summary tables over accepted spectra."""
    ms1_count = 0
    ms2_count = 0
    unknown_ms_level_count = 0
    charge_counts: dict[str, int] = {}
    precursor_counts: dict[str, int] = {}
    peak_counts: dict[str, int] = {}
    retention_times: list[float] = []

    mz_buckets = (
        ("0-399", 0.0, 399.999999),
        ("400-599", 400.0, 599.999999),
        ("600-799", 600.0, 799.999999),
        ("800-999", 800.0, 999.999999),
        ("1000+", 1000.0, None),
    )
    peak_buckets = (
        ("1-24", 1, 24),
        ("25-49", 25, 49),
        ("50-99", 50, 99),
        ("100-199", 100, 199),
        ("200+", 200, None),
    )

    ms_level_policy = "reported"
    for spectrum in spectra:
        ms_level = spectrum.ms_level
        if source_kind == "mgf" and ms_level is None:
            ms_level_policy = "mgf_assumed_ms2"
            ms2_count += 1
        elif ms_level == 1:
            ms1_count += 1
        elif ms_level == 2:
            ms2_count += 1
        else:
            unknown_ms_level_count += 1

        if spectrum.precursor_charge is None:
            charge_key = "unknown"
        elif spectrum.precursor_charge >= 5:
            charge_key = "5+"
        else:
            charge_key = str(spectrum.precursor_charge)
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1

        precursor_bucket = _bucket_float(
            spectrum.precursor_mz,
            buckets=mz_buckets,
        )
        precursor_counts[precursor_bucket] = (
            precursor_counts.get(precursor_bucket, 0) + 1
        )

        peak_bucket = _bucket_count(
            len(spectrum.peaks),
            buckets=peak_buckets,
        )
        peak_counts[peak_bucket] = peak_counts.get(peak_bucket, 0) + 1

        if spectrum.retention_time_seconds is not None:
            retention_times.append(spectrum.retention_time_seconds)

    charge_distribution = tuple(
        SpectrumDistributionRow(bucket=bucket, count=charge_counts.get(bucket, 0))
        for bucket in ("unknown", "1", "2", "3", "4", "5+")
        if bucket != "5+" or charge_counts.get("5+", 0) > 0
    )

    precursor_distribution = tuple(
        SpectrumDistributionRow(bucket=label, count=precursor_counts.get(label, 0))
        for label, _lower, _upper in mz_buckets
    )
    peak_distribution = tuple(
        SpectrumDistributionRow(bucket=label, count=peak_counts.get(label, 0))
        for label, _lower, _upper in peak_buckets
    )

    return SpectrumSummaryTableReport(
        source_kind=source_kind,
        ms_level_policy=ms_level_policy,
        spectrum_count=len(spectra),
        rejected_count=rejected_count,
        ms1_spectrum_count=ms1_count,
        ms2_spectrum_count=ms2_count,
        unknown_ms_level_count=unknown_ms_level_count,
        retention_time_min_seconds=min(retention_times) if retention_times else None,
        retention_time_max_seconds=max(retention_times) if retention_times else None,
        charge_distribution=charge_distribution,
        precursor_mz_distribution=precursor_distribution,
        peak_count_distribution=peak_distribution,
    )


def _render_tsv(header: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()


def render_spectrum_summary_tsv(report: SpectrumSummaryTableReport) -> str:
    """Render one compact summary table for a spectrum run report."""
    return _render_tsv(
        (
            "source_kind",
            "ms_level_policy",
            "spectrum_count",
            "rejected_count",
            "ms1_spectrum_count",
            "ms2_spectrum_count",
            "unknown_ms_level_count",
            "retention_time_min_seconds",
            "retention_time_max_seconds",
        ),
        (
            (
                report.source_kind,
                report.ms_level_policy,
                report.spectrum_count,
                report.rejected_count,
                report.ms1_spectrum_count,
                report.ms2_spectrum_count,
                report.unknown_ms_level_count,
                report.retention_time_min_seconds,
                report.retention_time_max_seconds,
            ),
        ),
    )


def render_spectrum_distribution_tsv(
    rows: tuple[SpectrumDistributionRow, ...],
    *,
    distribution_name: str,
) -> str:
    """Render one stable spectrum distribution table."""
    return _render_tsv(
        ("distribution", "bucket", "count"),
        tuple((distribution_name, row.bucket, row.count) for row in rows),
    )


def render_spectrum_similarity_tsv(
    report: SpectrumLibrarySimilarityReport,
) -> str:
    """Render one stable ranked spectrum-similarity table."""
    return _render_tsv(
        (
            "rank",
            "reference_spectrum_id",
            "classification",
            "score",
            "matched_peak_count",
            "reference_peak_count",
            "query_peak_count",
            "reference_explained_intensity_fraction",
            "query_explained_intensity_fraction",
        ),
        tuple(
            (
                row.rank,
                row.reference_spectrum_id,
                row.classification.value,
                row.score,
                row.matched_peak_count,
                row.reference_peak_count,
                row.query_peak_count,
                row.reference_explained_intensity_fraction,
                row.query_explained_intensity_fraction,
            )
            for row in report.matches
        ),
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
        pepmass = f"PEPMASS={spectrum.precursor_mz:.6f}".rstrip("0").rstrip(".")
        if spectrum.precursor_intensity is not None:
            pepmass += " " + f"{spectrum.precursor_intensity:.6f}".rstrip("0").rstrip(
                "."
            )
        lines.append(pepmass)
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


def build_precursor_mass_error_report(
    queries: tuple[PrecursorMassErrorQuery, ...],
    *,
    registry: ModificationRegistryDocument | None = None,
    max_isotope_offset: int = 3,
) -> PrecursorMassErrorReport:
    """Build a precursor mass-error report over one set of observations."""
    observations: list[PrecursorMassErrorObservation] = []
    charge_counts: dict[str, int] = {}
    ppm_counts: dict[str, int] = {}
    isotope_counts: dict[str, int] = {}
    delta_ppm_values: list[float] = []
    delta_da_values: list[float] = []
    abs_ppm_values: list[float] = []

    ppm_buckets = (
        ("0-5", 0.0, 5.0),
        ("5-10", 5.0, 10.0),
        ("10-20", 10.0, 20.0),
        ("20-50", 20.0, 50.0),
        ("50+", 50.0, None),
    )

    for query in queries:
        theoretical_mz = calculate_peptide_mz(
            query.peptide,
            charge=query.charge,
            registry=registry,
        )
        error = calculate_precursor_mass_error(
            observed_mz=query.observed_mz,
            theoretical_mz=theoretical_mz,
        )
        advisory = detect_precursor_isotope_offset_advisory(
            observed_mz=query.observed_mz,
            theoretical_mz=theoretical_mz,
            charge=query.charge,
            max_offset=max_isotope_offset,
        )
        observations.append(
            PrecursorMassErrorObservation(
                peptide=query.peptide,
                canonical_peptide=canonicalize_modified_peptide(
                    query.peptide,
                    registry=registry,
                ),
                observed_mz=query.observed_mz,
                theoretical_mz=theoretical_mz,
                charge=query.charge,
                spectrum_id=query.spectrum_id,
                delta_da=error.delta_da,
                delta_ppm=error.delta_ppm,
                absolute_delta_da=abs(error.delta_da),
                absolute_delta_ppm=abs(error.delta_ppm),
                isotope_offset_advisory=advisory,
            )
        )
        charge_key = str(query.charge) if query.charge < 5 else "5+"
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1

        ppm_bucket = _bucket_float(abs(error.delta_ppm), buckets=ppm_buckets)
        ppm_counts[ppm_bucket] = ppm_counts.get(ppm_bucket, 0) + 1

        isotope_key = str(advisory.recommended_offset)
        isotope_counts[isotope_key] = isotope_counts.get(isotope_key, 0) + 1

        delta_ppm_values.append(error.delta_ppm)
        delta_da_values.append(error.delta_da)
        abs_ppm_values.append(abs(error.delta_ppm))

    charge_distribution = tuple(
        PrecursorMassErrorDistributionRow(
            bucket=bucket,
            count=charge_counts.get(bucket, 0),
        )
        for bucket in ("1", "2", "3", "4", "5+")
        if bucket != "5+" or charge_counts.get("5+", 0) > 0
    )
    ppm_distribution = tuple(
        PrecursorMassErrorDistributionRow(
            bucket=label,
            count=ppm_counts.get(label, 0),
        )
        for label, _lower, _upper in ppm_buckets
    )
    isotope_distribution = tuple(
        PrecursorMassErrorDistributionRow(
            bucket=str(offset),
            count=isotope_counts.get(str(offset), 0),
        )
        for offset in range(max_isotope_offset + 1)
    )

    sorted_delta_ppm = sorted(delta_ppm_values)
    sorted_abs_ppm = sorted(abs_ppm_values)

    return PrecursorMassErrorReport(
        observation_count=len(observations),
        charge_distribution=charge_distribution,
        ppm_error_distribution=ppm_distribution,
        isotope_offset_distribution=isotope_distribution,
        mean_delta_ppm=(
            sum(delta_ppm_values) / len(delta_ppm_values) if delta_ppm_values else None
        ),
        mean_delta_da=(
            sum(delta_da_values) / len(delta_da_values) if delta_da_values else None
        ),
        median_delta_ppm=(
            sorted_delta_ppm[len(sorted_delta_ppm) // 2] if sorted_delta_ppm else None
        ),
        median_abs_delta_ppm=(
            sorted_abs_ppm[len(sorted_abs_ppm) // 2] if sorted_abs_ppm else None
        ),
        max_abs_delta_ppm=max(sorted_abs_ppm) if sorted_abs_ppm else None,
        observations=tuple(observations),
    )


def render_precursor_mass_error_summary_tsv(report: PrecursorMassErrorReport) -> str:
    """Render one summary row for a precursor mass-error report."""
    return _render_tsv(
        (
            "observation_count",
            "mean_delta_ppm",
            "mean_delta_da",
            "median_delta_ppm",
            "median_abs_delta_ppm",
            "max_abs_delta_ppm",
        ),
        (
            (
                report.observation_count,
                report.mean_delta_ppm,
                report.mean_delta_da,
                report.median_delta_ppm,
                report.median_abs_delta_ppm,
                report.max_abs_delta_ppm,
            ),
        ),
    )


def render_precursor_mass_error_distribution_tsv(
    rows: tuple[PrecursorMassErrorDistributionRow, ...],
    *,
    distribution_name: str,
) -> str:
    """Render one stable precursor mass-error distribution table."""
    return _render_tsv(
        ("distribution", "bucket", "count"),
        tuple((distribution_name, row.bucket, row.count) for row in rows),
    )


def render_precursor_mass_error_observations_tsv(
    observations: tuple[PrecursorMassErrorObservation, ...],
) -> str:
    """Render per-observation precursor mass-error rows."""
    return _render_tsv(
        (
            "spectrum_id",
            "peptide",
            "canonical_peptide",
            "charge",
            "observed_mz",
            "theoretical_mz",
            "delta_da",
            "delta_ppm",
            "absolute_delta_da",
            "absolute_delta_ppm",
            "recommended_isotope_offset",
        ),
        tuple(
            (
                observation.spectrum_id,
                observation.peptide,
                observation.canonical_peptide,
                observation.charge,
                observation.observed_mz,
                observation.theoretical_mz,
                observation.delta_da,
                observation.delta_ppm,
                observation.absolute_delta_da,
                observation.absolute_delta_ppm,
                observation.isotope_offset_advisory.recommended_offset,
            )
            for observation in observations
        ),
    )


def calculate_spectral_similarity(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float | None = None,
    bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
) -> SpectralSimilarityScore:
    """Calculate a basic matched-peak spectral similarity score."""
    matching_mode, resolved_tolerance_da, resolved_bin_width_da = (
        _resolve_similarity_matching_strategy(
            tolerance_da=tolerance_da,
            bin_width_da=bin_width_da,
        )
    )
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

    if matching_mode is SpectrumSimilarityMatchingMode.BINNED:
        matched_reference, matched_query, reference_total, query_total = (
            _match_binned_similarity_vectors(
                reference_spectrum,
                query_spectrum,
                bin_width_da=resolved_bin_width_da or 1.0,
            )
        )
    else:
        matched_reference, matched_query, reference_total, query_total = (
            _match_tolerance_similarity_vectors(
                reference_spectrum,
                query_spectrum,
                tolerance_da=resolved_tolerance_da or 0.02,
            )
        )

    dot_product = sum(
        reference * query
        for reference, query in zip(matched_reference, matched_query, strict=True)
    )
    if method is SpectralSimilarityMethod.DOT_PRODUCT:
        score = dot_product
    else:
        reference_norm = sum(value * value for value in reference_total) ** 0.5
        query_norm = sum(value * value for value in query_total) ** 0.5
        score = (
            0.0
            if reference_norm == 0.0 or query_norm == 0.0
            else dot_product / (reference_norm * query_norm)
        )
    matched_reference_intensity = sum(matched_reference)
    matched_query_intensity = sum(matched_query)
    total_reference_intensity = sum(reference_total)
    total_query_intensity = sum(query_total)
    return SpectralSimilarityScore(
        method=method,
        mode=mode,
        matching_mode=matching_mode,
        tolerance_da=resolved_tolerance_da,
        bin_width_da=resolved_bin_width_da,
        score=score,
        matched_peak_count=len(matched_reference),
        reference_peak_count=len(reference_spectrum.peaks),
        query_peak_count=len(query_spectrum.peaks),
        reference_explained_intensity_fraction=(
            0.0
            if total_reference_intensity == 0.0
            else matched_reference_intensity / total_reference_intensity
        ),
        query_explained_intensity_fraction=(
            0.0
            if total_query_intensity == 0.0
            else matched_query_intensity / total_query_intensity
        ),
    )


def build_spectrum_similarity_comparison_report(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float | None = None,
    bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
) -> SpectrumSimilarityComparisonReport:
    """Build a reviewer-facing comparison between two spectra."""
    score = calculate_spectral_similarity(
        reference_spectrum,
        query_spectrum,
        tolerance_da=tolerance_da,
        bin_width_da=bin_width_da,
        method=method,
        mode=mode,
        top_n=top_n,
    )
    parameters = SpectrumSimilarityParameters(
        method=score.method,
        mode=score.mode,
        matching_mode=score.matching_mode,
        tolerance_da=score.tolerance_da,
        bin_width_da=score.bin_width_da,
        top_n=top_n,
    )
    classification = _classify_spectral_similarity(score)
    report = SpectrumSimilarityComparisonReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectrum_similarity_comparison",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        parameters=parameters,
        reference_spectrum_id=reference_spectrum.spectrum_id,
        query_spectrum_id=query_spectrum.spectrum_id,
        classification=classification,
        score=score.score,
        matched_peak_count=score.matched_peak_count,
        reference_peak_count=score.reference_peak_count,
        query_peak_count=score.query_peak_count,
        reference_explained_intensity_fraction=(
            score.reference_explained_intensity_fraction
        ),
        query_explained_intensity_fraction=score.query_explained_intensity_fraction,
        interpretation=_describe_spectral_similarity(classification, score),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
    )


def build_spectrum_library_similarity_report(
    query_spectrum: SpectrumModel,
    reference_spectra: tuple[SpectrumModel, ...],
    *,
    tolerance_da: float | None = None,
    bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.RAW,
    top_n: int | None = None,
    max_matches: int | None = None,
) -> SpectrumLibrarySimilarityReport:
    """Rank one query spectrum against a reference collection."""
    scores = [
        (
            reference,
            calculate_spectral_similarity(
                reference,
                query_spectrum,
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=method,
                mode=mode,
                top_n=top_n,
            ),
        )
        for reference in reference_spectra
    ]
    ranked = sorted(
        scores,
        key=lambda item: (
            -item[1].score,
            -item[1].matched_peak_count,
            item[0].spectrum_id,
        ),
    )
    if max_matches is not None:
        ranked = ranked[:max_matches]

    matches: list[SpectrumLibrarySimilarityMatch] = []
    duplicate_like_count = 0
    similar_count = 0
    for rank, (reference, score) in enumerate(ranked, start=1):
        classification = _classify_spectral_similarity(score)
        if classification is SpectrumSimilarityClassification.DUPLICATE_LIKE:
            duplicate_like_count += 1
        if classification in {
            SpectrumSimilarityClassification.DUPLICATE_LIKE,
            SpectrumSimilarityClassification.SIMILAR,
        }:
            similar_count += 1
        matches.append(
            SpectrumLibrarySimilarityMatch(
                rank=rank,
                reference_spectrum_id=reference.spectrum_id,
                classification=classification,
                score=score.score,
                matched_peak_count=score.matched_peak_count,
                reference_peak_count=score.reference_peak_count,
                query_peak_count=score.query_peak_count,
                reference_explained_intensity_fraction=(
                    score.reference_explained_intensity_fraction
                ),
                query_explained_intensity_fraction=(
                    score.query_explained_intensity_fraction
                ),
            )
        )

    parameters = SpectrumSimilarityParameters(
        method=method,
        mode=mode,
        matching_mode=(
            ranked[0][1].matching_mode
            if ranked
            else SpectrumSimilarityMatchingMode.TOLERANCE
        ),
        tolerance_da=ranked[0][1].tolerance_da if ranked else tolerance_da,
        bin_width_da=ranked[0][1].bin_width_da if ranked else bin_width_da,
        top_n=top_n,
    )
    report = SpectrumLibrarySimilarityReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectrum_library_similarity_report",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        parameters=parameters,
        query_spectrum_id=query_spectrum.spectrum_id,
        candidate_count=len(reference_spectra),
        duplicate_like_match_count=duplicate_like_count,
        similar_match_count=similar_count,
        matches=tuple(matches),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
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


def _resolve_similarity_matching_strategy(
    *,
    tolerance_da: float | None,
    bin_width_da: float | None,
) -> tuple[SpectrumSimilarityMatchingMode, float | None, float | None]:
    if tolerance_da is not None and bin_width_da is not None:
        raise ValueError("choose either tolerance_da or bin_width_da, not both")
    if bin_width_da is not None:
        if bin_width_da <= 0:
            raise ValueError("bin_width_da must be greater than zero")
        return SpectrumSimilarityMatchingMode.BINNED, None, bin_width_da
    if tolerance_da is None:
        tolerance_da = 0.02
    if tolerance_da <= 0:
        raise ValueError("tolerance_da must be greater than zero")
    return SpectrumSimilarityMatchingMode.TOLERANCE, tolerance_da, None


def _match_tolerance_similarity_vectors(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    tolerance_da: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
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
    return (
        matched_reference,
        matched_query,
        [peak.intensity for peak in reference_spectrum.peaks],
        [peak.intensity for peak in query_spectrum.peaks],
    )


def _match_binned_similarity_vectors(
    reference_spectrum: SpectrumModel,
    query_spectrum: SpectrumModel,
    *,
    bin_width_da: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
    reference_bins = _bin_similarity_peaks(
        reference_spectrum, bin_width_da=bin_width_da
    )
    query_bins = _bin_similarity_peaks(query_spectrum, bin_width_da=bin_width_da)
    shared_bins = tuple(sorted(set(reference_bins) & set(query_bins)))
    matched_reference = [reference_bins[index] for index in shared_bins]
    matched_query = [query_bins[index] for index in shared_bins]
    return (
        matched_reference,
        matched_query,
        list(reference_bins.values()),
        list(query_bins.values()),
    )


def _bin_similarity_peaks(
    spectrum: SpectrumModel,
    *,
    bin_width_da: float,
) -> dict[int, float]:
    bins: dict[int, float] = {}
    for peak in spectrum.peaks:
        index = int(round(peak.mz / bin_width_da))
        bins[index] = bins.get(index, 0.0) + peak.intensity
    return dict(sorted(bins.items()))


def _classify_spectral_similarity(
    score: SpectralSimilarityScore,
) -> SpectrumSimilarityClassification:
    if score.reference_peak_count == 0 or score.query_peak_count == 0:
        return SpectrumSimilarityClassification.INSUFFICIENT_SIGNAL
    if score.matched_peak_count == 0:
        return SpectrumSimilarityClassification.DISTINCT
    if (
        score.score >= 0.98
        and min(
            score.reference_explained_intensity_fraction,
            score.query_explained_intensity_fraction,
        )
        >= 0.9
    ):
        return SpectrumSimilarityClassification.DUPLICATE_LIKE
    if score.score >= 0.7 and score.matched_peak_count >= 2:
        return SpectrumSimilarityClassification.SIMILAR
    return SpectrumSimilarityClassification.DISTINCT


def _describe_spectral_similarity(
    classification: SpectrumSimilarityClassification,
    score: SpectralSimilarityScore,
) -> str:
    if classification is SpectrumSimilarityClassification.INSUFFICIENT_SIGNAL:
        return "One or both spectra have no usable peaks after preprocessing."
    if classification is SpectrumSimilarityClassification.DUPLICATE_LIKE:
        return (
            "The spectra are duplicate-like under the selected preprocessing and "
            "matching policy."
        )
    if classification is SpectrumSimilarityClassification.SIMILAR:
        return (
            "The spectra share substantial fragment evidence and are suitable for "
            "similar-spectrum or library-style review."
        )
    if score.matched_peak_count == 0:
        return "No shared peaks were matched under the selected comparison policy."
    return "The spectra share limited evidence and should be treated as distinct."


def _canonical_peptide_text(peptide: str | ParsedModifiedPeptide) -> str:
    if isinstance(peptide, ParsedModifiedPeptide):
        return canonicalize_modified_peptide(peptide)
    return canonicalize_modified_peptide(peptide)


def _fragment_label(fragment: FragmentIon) -> str:
    return f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}"


def _resolve_annotation_tolerance(
    *,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> tuple[SpectrumAnnotationToleranceUnit, float | None, float | None]:
    if tolerance_da is not None and tolerance_ppm is not None:
        raise ValueError("choose either tolerance_da or tolerance_ppm, not both")
    if tolerance_ppm is not None:
        if tolerance_ppm <= 0:
            raise ValueError("tolerance_ppm must be greater than zero")
        return SpectrumAnnotationToleranceUnit.PPM, None, tolerance_ppm
    if tolerance_da is None or tolerance_da <= 0:
        raise ValueError("tolerance_da must be greater than zero")
    return SpectrumAnnotationToleranceUnit.DA, tolerance_da, None


def _matches_fragment_tolerance(
    *,
    observed_mz: float,
    fragment_mz: float,
    tolerance_unit: SpectrumAnnotationToleranceUnit,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> bool:
    error_da = observed_mz - fragment_mz
    if tolerance_unit is SpectrumAnnotationToleranceUnit.PPM:
        if tolerance_ppm is None:
            raise ValueError("tolerance_ppm must be resolved for ppm annotation")
        return abs((error_da / fragment_mz) * 1_000_000.0) <= tolerance_ppm
    if tolerance_da is None:
        raise ValueError("tolerance_da must be resolved for dalton annotation")
    return abs(error_da) <= tolerance_da


def annotate_spectrum_fragments(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    tolerance_da: float | None = 0.5,
    tolerance_ppm: float | None = None,
    include_neutral_losses: bool = True,
) -> SpectrumAnnotation:
    """Match theoretical fragments against observed peaks within one tolerance."""
    canonical = _canonical_peptide_text(peptide)
    peak_match_report = build_spectrum_peak_match_report(
        spectrum,
        peptide=peptide,
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
        include_neutral_losses=include_neutral_losses,
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
        tolerance_unit=SpectrumAnnotationToleranceUnit(
            peak_match_report.tolerance_mode.value
        ),
        tolerance_da=peak_match_report.tolerance_da,
        tolerance_ppm=peak_match_report.tolerance_ppm,
        matches=tuple(
            SpectrumAnnotationMatch(
                fragment=match.fragment,
                fragment_label=match.fragment_label,
                observed_mz=match.observed_mz,
                observed_intensity=match.observed_intensity,
                mass_error_da=match.mass_error_da,
                mass_error_ppm=match.mass_error_ppm,
            )
            for match in peak_match_report.matches
        ),
        unmatched_peaks=tuple(
            SpectrumAnnotationUnmatchedPeak(
                mz=peak.mz,
                intensity=peak.intensity,
            )
            for peak in peak_match_report.unmatched_peaks
        ),
        ambiguity_warnings=tuple(
            SpectrumAnnotationAmbiguityWarning(
                kind=SpectrumAnnotationAmbiguityKind(warning.kind.value),
                fragment_labels=warning.fragment_labels,
                peak_mzs=warning.peak_mzs,
                tolerance_unit=SpectrumAnnotationToleranceUnit(
                    warning.tolerance_mode.value
                ),
                tolerance_da=warning.tolerance_da,
                tolerance_ppm=warning.tolerance_ppm,
                note=warning.note,
            )
            for warning in peak_match_report.ambiguity_warnings
        ),
        matched_peak_count=peak_match_report.matched_peak_count,
        explained_intensity=peak_match_report.explained_intensity,
        total_observed_intensity=peak_match_report.total_observed_intensity,
        explained_intensity_fraction=peak_match_report.explained_intensity_fraction,
        unmatched_peak_count=peak_match_report.unmatched_peak_count,
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
                "tolerance_mode",
                "series",
                "ordinal",
                "fragment_charge",
                "span_start",
                "span_end",
                "fragment_sequence",
                "fragment_mz",
                "neutral_loss",
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
                    annotation.tolerance_unit.value,
                    match.fragment.series.value,
                    match.fragment.ordinal,
                    match.fragment.charge,
                    match.fragment.span_start,
                    match.fragment.span_end,
                    match.fragment.sequence,
                    match.fragment.mz_monoisotopic,
                    (
                        None
                        if match.fragment.neutral_loss is None
                        else match.fragment.neutral_loss
                    ),
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
    tolerance_da: float | None = 0.5,
    tolerance_ppm: float | None = None,
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
        tolerance_ppm=tolerance_ppm,
        include_neutral_losses=include_neutral_losses,
    )
    tolerance_unit, resolved_tolerance_da, resolved_tolerance_ppm = (
        _resolve_annotation_tolerance(
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
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
            tolerance_unit=tolerance_unit,
            tolerance_da=resolved_tolerance_da,
            tolerance_ppm=resolved_tolerance_ppm,
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


def write_annotated_spectrum_bundle(
    bundle: AnnotatedSpectrumBundle,
    path: Path,
) -> None:
    """Write one annotated spectrum bundle as stable JSON."""
    path.write_text(
        json.dumps(bundle.to_dict(), sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def export_annotated_spectrum_bundle(
    bundle: AnnotatedSpectrumBundle,
    path: Path,
) -> None:
    """Compatibility wrapper for the legacy annotated spectrum bundle export name."""

    write_annotated_spectrum_bundle(bundle, path)
