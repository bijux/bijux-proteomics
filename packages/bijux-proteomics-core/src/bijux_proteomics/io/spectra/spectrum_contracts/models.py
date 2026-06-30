# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum contract models and enums."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.chemistry.fragments import FragmentIon
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


__all__ = [
    "AnnotatedSpectrumBundle",
    "MgfParseReport",
    "PeakNormalizationPolicy",
    "PrecursorIsotopeOffsetAdvisory",
    "PrecursorIsotopeOffsetCandidate",
    "PrecursorMassError",
    "PrecursorMassErrorDistributionRow",
    "PrecursorMassErrorObservation",
    "PrecursorMassErrorQuery",
    "PrecursorMassErrorReport",
    "RejectedSpectrumBlock",
    "SpectralSimilarityMethod",
    "SpectralSimilarityScore",
    "SpectrumAnnotation",
    "SpectrumAnnotationAmbiguityKind",
    "SpectrumAnnotationAmbiguityWarning",
    "SpectrumAnnotationMatch",
    "SpectrumAnnotationParameters",
    "SpectrumAnnotationToleranceUnit",
    "SpectrumAnnotationUnmatchedPeak",
    "SpectrumCollectionSummary",
    "SpectrumDistributionRow",
    "SpectrumFilterReport",
    "SpectrumLibrarySimilarityMatch",
    "SpectrumLibrarySimilarityReport",
    "SpectrumLookupIndex",
    "SpectrumMetrics",
    "SpectrumModel",
    "SpectrumPeak",
    "SpectrumPlotPayload",
    "SpectrumPlotPeak",
    "SpectrumProvenanceManifest",
    "SpectrumSimilarityClassification",
    "SpectrumSimilarityComparisonReport",
    "SpectrumSimilarityMatchingMode",
    "SpectrumSimilarityMode",
    "SpectrumSimilarityParameters",
    "SpectrumSummaryTableReport",
    "SpectrumValidationIssue",
]
