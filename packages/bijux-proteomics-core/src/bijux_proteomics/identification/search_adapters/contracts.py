# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared search-adapter contracts over normalized PSM parsing."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    CalibrationPlotData,
    FdrAuditTrail,
    PsmParseReport,
    PsmRecord,
    SearchResultColumnMapping,
    SearchResultProvenanceManifest,
    SearchResultValidationIssue,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class ScoreOrientation(StrEnum):
    """Whether a native engine score is higher-better or lower-better."""

    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"


class SearchAdapterKind(StrEnum):
    """Built-in search adapter identifiers."""

    COMET = "comet"
    MSFRAGGER = "msfragger"
    SAGE = "sage"
    MAXQUANT_EVIDENCE = "maxquant-evidence"
    DIANN = "diann"
    SPECTRONAUT = "spectronaut"
    GENERIC = "generic"


class SearchToleranceUnit(StrEnum):
    """Stable tolerance units for parsed engine parameter files."""

    PPM = "ppm"
    DA = "da"


class SearchScoreFamily(StrEnum):
    """Explicit native score families across search result engines."""

    EXPECTATION_VALUE = "expectation_value"
    HYPERSCORE = "hyperscore"
    DISCRIMINANT_SCORE = "discriminant_score"
    ENGINE_SCORE = "engine_score"
    Q_VALUE = "q_value"
    CONFIDENCE_SCORE = "confidence_score"
    GENERIC_NUMERIC = "generic_numeric"


class SearchResultFamily(StrEnum):
    """Explicit search result families across database and library workflows."""

    DATABASE_TARGET_DECOY = "database_target_decoy"
    LIBRARY_SEARCH = "library_search"
    MIXED_TARGET_LIBRARY = "mixed_target_library"


class SearchAdapterManifest(JsonModel):
    """Stable contract describing one search adapter."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    display_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    score_orientation: ScoreOrientation
    score_family: SearchScoreFamily = SearchScoreFamily.GENERIC_NUMERIC
    result_family: SearchResultFamily = SearchResultFamily.DATABASE_TARGET_DECOY
    native_columns: tuple[str, ...] = Field(default_factory=tuple)
    mapping: SearchResultColumnMapping | None = None
    default_decoy_policy: TargetDecoyLabelPolicy = Field(
        default_factory=TargetDecoyLabelPolicy
    )
    supported_extensions: tuple[str, ...] = Field(default_factory=tuple)
    supports_q_value: bool = False
    supports_explicit_decoy_label: bool = False
    supports_protein_refs: bool = False
    supports_config_hash: bool = False
    supports_external_execution: bool = False


class SearchAdapterDialectManifest(JsonModel):
    """One controlled adapter dialect extension over a base engine family."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    dialect_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    score_orientation: ScoreOrientation | None = None
    score_family: SearchScoreFamily = SearchScoreFamily.GENERIC_NUMERIC
    result_family: SearchResultFamily = SearchResultFamily.DATABASE_TARGET_DECOY
    native_columns: tuple[str, ...] = Field(default_factory=tuple)
    mapping: SearchResultColumnMapping


class SearchAdapterCapability(JsonModel):
    """Compact capability row for one search adapter."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    display_name: str = Field(..., min_length=1)
    score_orientation: ScoreOrientation
    score_family: SearchScoreFamily
    result_family: SearchResultFamily
    supports_q_value: bool
    supports_explicit_decoy_label: bool
    supports_protein_refs: bool
    supports_config_hash: bool
    supports_external_execution: bool
    native_columns: tuple[str, ...] = Field(default_factory=tuple)


class SearchAdapterNormalizationReport(JsonModel):
    """Normalized records plus the adapter manifest that produced them."""

    model_config = ConfigDict(extra="forbid")

    adapter_manifest: SearchAdapterManifest
    family_policy: SearchResultFamilyPolicy
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    parse_report: PsmParseReport
    normalized_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    evidence_rows: tuple[SearchNormalizedEvidenceEntry, ...] = Field(
        default_factory=tuple
    )


class SearchAdapterProvenanceManifest(JsonModel):
    """Stable provenance for one adapter normalization pass."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    adapter_kind: SearchAdapterKind
    adapter_name: str = Field(..., min_length=1)
    adapter_version: str | None = None
    source_path: str = Field(..., min_length=1)
    source_sha256: str = Field(..., min_length=64, max_length=64)
    config_path: str | None = None
    config_sha256: str | None = None
    parameter_report: SearchParameterReport | None = None
    result_family: SearchResultFamily
    family_policy: SearchResultFamilyPolicy
    native_columns: tuple[str, ...] = Field(default_factory=tuple)
    score_orientation: ScoreOrientation
    parse_provenance: SearchResultProvenanceManifest


class SearchNormalizedEvidenceEntry(JsonModel):
    """One preserved engine row plus its normalized adapter outcome."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    accepted: bool
    raw_fields: dict[str, str] = Field(default_factory=dict)
    mapped_field_values: dict[str, str] = Field(default_factory=dict)
    unmapped_native_fields: dict[str, str] = Field(default_factory=dict)
    normalized_record: PsmRecord | None = None
    issues: tuple[SearchResultValidationIssue, ...] = Field(default_factory=tuple)


class SearchResultFamilyPolicy(JsonModel):
    """Explicit policy expectations for one search result family."""

    model_config = ConfigDict(extra="forbid")

    result_family: SearchResultFamily
    requires_target_decoy_evidence: bool
    requires_protein_references: bool
    allows_library_style_scores: bool
    note: str = Field(..., min_length=1)


class SearchModificationDefinition(JsonModel):
    """One fixed or variable search modification declaration."""

    model_config = ConfigDict(extra="forbid")

    site: str = Field(..., min_length=1)
    mass_delta: float
    variable: bool
    source_key: str = Field(..., min_length=1)


class SearchParameterReport(JsonModel):
    """Parsed search-parameter file normalized onto a stable contract."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    adapter_name: str = Field(..., min_length=1)
    enzyme: str = Field(..., min_length=1)
    missed_cleavages: int | None = Field(default=None, ge=0)
    precursor_tolerance: float | None = None
    precursor_tolerance_unit: SearchToleranceUnit | None = None
    fragment_tolerance: float | None = None
    fragment_tolerance_unit: SearchToleranceUnit | None = None
    database_path: str | None = None
    decoy_prefix: str | None = None
    has_decoy_strategy: bool = False
    fixed_modifications: tuple[SearchModificationDefinition, ...] = Field(
        default_factory=tuple
    )
    variable_modifications: tuple[SearchModificationDefinition, ...] = Field(
        default_factory=tuple
    )
    raw_fields: dict[str, str] = Field(default_factory=dict)


class SearchConfigValidationIssue(JsonModel):
    """One stable validation issue for a parsed engine configuration."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")


class SearchConfigValidationReport(JsonModel):
    """Validation result for one parsed search-parameter file."""

    model_config = ConfigDict(extra="forbid")

    parameters: SearchParameterReport
    valid: bool
    issues: tuple[SearchConfigValidationIssue, ...] = Field(default_factory=tuple)


class SearchParameterDifferenceEntry(JsonModel):
    """One normalized difference between two search parameter reports."""

    model_config = ConfigDict(extra="forbid")

    field_name: str = Field(..., min_length=1)
    left_value: str | None = None
    right_value: str | None = None
    severity: str = Field(..., pattern="^(compatible|different)$")
    note: str = Field(..., min_length=1)


class SearchParameterComparisonReport(JsonModel):
    """Stable comparison between two normalized search parameter reports."""

    model_config = ConfigDict(extra="forbid")

    left_adapter_kind: SearchAdapterKind
    right_adapter_kind: SearchAdapterKind
    left_adapter_name: str = Field(..., min_length=1)
    right_adapter_name: str = Field(..., min_length=1)
    comparable: bool
    differences: tuple[SearchParameterDifferenceEntry, ...] = Field(
        default_factory=tuple
    )


class SearchMergeAgreementStatus(StrEnum):
    """Agreement state across multiple engine observations for one spectrum."""

    EXACT_MATCH = "exact_match"
    PEPTIDE_CONFLICT = "peptide_conflict"
    CHARGE_CONFLICT = "charge_conflict"
    LABEL_CONFLICT = "label_conflict"
    PARTIAL_COVERAGE = "partial_coverage"


class SearchEngineObservation(JsonModel):
    """One engine-specific PSM observation preserved during result merging."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    adapter_name: str = Field(..., min_length=1)
    score_family: SearchScoreFamily
    result_family: SearchResultFamily
    normalized_score: float
    q_value: float | None = Field(default=None, ge=0.0)
    record: PsmRecord


class MergedSearchSpectrumEntry(JsonModel):
    """Merged per-spectrum search evidence with per-engine uncertainty retained."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    observations: tuple[SearchEngineObservation, ...] = Field(default_factory=tuple)
    agreement_status: SearchMergeAgreementStatus
    consensus_peptide: str | None = None
    consensus_charge: int | None = Field(default=None, ge=1)
    uncertainty_note: str = Field(..., min_length=1)


class SearchResultMergeReport(JsonModel):
    """Stable multi-engine merge report that preserves engine-specific uncertainty."""

    model_config = ConfigDict(extra="forbid")

    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    merged_entries: tuple[MergedSearchSpectrumEntry, ...] = Field(default_factory=tuple)
    exact_agreement_count: int = Field(..., ge=0)
    conflict_count: int = Field(..., ge=0)
    partial_coverage_count: int = Field(..., ge=0)


class SearchMergeCompatibilityIssue(JsonModel):
    """One compatibility issue surfaced before multi-engine merge."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: str = Field(..., pattern="^(error|warning)$")
    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)


class SearchMergeCompatibilityReport(JsonModel):
    """Compatibility gate for multi-engine merge workflows."""

    model_config = ConfigDict(extra="forbid")

    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    compatible: bool
    issues: tuple[SearchMergeCompatibilityIssue, ...] = Field(default_factory=tuple)


class ExternalEngineDisagreementKind(StrEnum):
    """Primary disagreement categories across external engine outputs."""

    MISSING_EVIDENCE = "missing_evidence"
    PEPTIDE_CONFLICT = "peptide_conflict"
    CHARGE_CONFLICT = "charge_conflict"
    LABEL_CONFLICT = "label_conflict"
    CONFIDENCE_GAP = "confidence_gap"


class ExternalEngineDisagreementEntry(JsonModel):
    """One disagreement entry across two or more engine outputs."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    kind: ExternalEngineDisagreementKind
    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    message: str = Field(..., min_length=1)
    normalized_score_delta: float | None = Field(default=None, ge=0.0)


class ExternalEngineDisagreementReport(JsonModel):
    """Stable disagreement report over multiple normalized adapter outputs."""

    model_config = ConfigDict(extra="forbid")

    adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    entries: tuple[ExternalEngineDisagreementEntry, ...] = Field(default_factory=tuple)
    disagreement_counts: dict[str, int] = Field(default_factory=dict)


class SearchRegressionFixtureKind(StrEnum):
    """Fixture categories within the search adapter regression corpus."""

    ENGINE_EXPORT_LIKE = "engine_export_like"
    PIPELINE_EXPORT = "pipeline_export"
    PARAMETER_FILE = "parameter_file"
    FAILURE_CASE = "failure_case"
    MAPPING_CONTROL = "mapping_control"
    OTHER = "other"


class SearchRegressionCorpusEntry(JsonModel):
    """One stable entry inside a search adapter regression corpus manifest."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    adapter_kind: SearchAdapterKind | None = None
    fixture_kind: SearchRegressionFixtureKind
    note: str = Field(..., min_length=1)


class SearchRegressionCorpusManifest(JsonModel):
    """Stable manifest over a search adapter regression corpus directory."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    corpus_root: str = Field(..., min_length=1)
    entries: tuple[SearchRegressionCorpusEntry, ...] = Field(default_factory=tuple)
    covered_adapter_kinds: tuple[SearchAdapterKind, ...] = Field(default_factory=tuple)
    engine_export_like_count: int = Field(..., ge=0)
    failure_case_count: int = Field(..., ge=0)


class SearchInputRefusalKind(StrEnum):
    """Reason a search input is refused before normalization proceeds."""

    MALFORMED_INPUT = "malformed_input"
    UNDER_SPECIFIED_INPUT = "under_specified_input"
    SCIENTIFIC_INCOMPATIBILITY = "scientific_incompatibility"


class SearchInputRefusal(JsonModel):
    """One explicit refusal emitted during search-input preflight assessment."""

    model_config = ConfigDict(extra="forbid")

    kind: SearchInputRefusalKind
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    remediation_hint: str = Field(..., min_length=1)


class SearchInputAssessmentReport(JsonModel):
    """Preflight assessment over one search input before normalization."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    dialect_id: str = Field(..., min_length=1)
    valid: bool
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    row_count: int = Field(..., ge=0)
    refusals: tuple[SearchInputRefusal, ...] = Field(default_factory=tuple)


class SearchResultComparabilityReport(JsonModel):
    """Comparability summary between two normalized search-result reports."""

    model_config = ConfigDict(extra="forbid")

    left_adapter_kind: SearchAdapterKind
    right_adapter_kind: SearchAdapterKind
    left_score_family: SearchScoreFamily
    right_score_family: SearchScoreFamily
    left_result_family: SearchResultFamily
    right_result_family: SearchResultFamily
    score_family_compatible: bool
    score_family_note: str = Field(..., min_length=1)
    left_total_psms: int = Field(..., ge=0)
    right_total_psms: int = Field(..., ge=0)
    shared_spectrum_count: int = Field(..., ge=0)
    left_only_spectrum_count: int = Field(..., ge=0)
    right_only_spectrum_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    exact_match_count: int = Field(..., ge=0)
    label_conflict_count: int = Field(..., ge=0)
    peptide_agreement_fraction: float = Field(..., ge=0.0, le=1.0)
    mean_normalized_score_delta: float = Field(..., ge=0.0)


class SearchAdapterConformanceCheck(JsonModel):
    """One conformance check over an adapter normalization run."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    passed: bool
    detail: str = Field(..., min_length=1)


class SearchAdapterFieldAccounting(JsonModel):
    """Field-level accounting over one adapter normalization pass."""

    model_config = ConfigDict(extra="forbid")

    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    mapped_columns: tuple[str, ...] = Field(default_factory=tuple)
    preserved_native_only_columns: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_columns: tuple[str, ...] = Field(default_factory=tuple)
    lost_columns: tuple[str, ...] = Field(default_factory=tuple)
    mapped_field_roles: dict[str, str] = Field(default_factory=dict)


class SearchAdapterConformanceReport(JsonModel):
    """Stable conformance report for one adapter normalization run."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    rejection_issue_counts: dict[str, int] = Field(default_factory=dict)
    field_accounting: SearchAdapterFieldAccounting
    checks: tuple[SearchAdapterConformanceCheck, ...] = Field(default_factory=tuple)
    passes: bool
    fdr_audit_trail: FdrAuditTrail | None = None
    calibration_plot: CalibrationPlotData | None = None


__all__ = [
    "ExternalEngineDisagreementEntry",
    "ExternalEngineDisagreementKind",
    "ExternalEngineDisagreementReport",
    "MergedSearchSpectrumEntry",
    "ScoreOrientation",
    "SearchAdapterCapability",
    "SearchAdapterConformanceCheck",
    "SearchAdapterConformanceReport",
    "SearchAdapterDialectManifest",
    "SearchAdapterFieldAccounting",
    "SearchAdapterKind",
    "SearchAdapterManifest",
    "SearchAdapterNormalizationReport",
    "SearchAdapterProvenanceManifest",
    "SearchConfigValidationIssue",
    "SearchConfigValidationReport",
    "SearchEngineObservation",
    "SearchInputAssessmentReport",
    "SearchInputRefusal",
    "SearchInputRefusalKind",
    "SearchMergeAgreementStatus",
    "SearchMergeCompatibilityIssue",
    "SearchMergeCompatibilityReport",
    "SearchModificationDefinition",
    "SearchNormalizedEvidenceEntry",
    "SearchParameterComparisonReport",
    "SearchParameterDifferenceEntry",
    "SearchParameterReport",
    "SearchRegressionCorpusEntry",
    "SearchRegressionCorpusManifest",
    "SearchRegressionFixtureKind",
    "SearchResultComparabilityReport",
    "SearchResultFamily",
    "SearchResultFamilyPolicy",
    "SearchResultMergeReport",
    "SearchScoreFamily",
    "SearchToleranceUnit",
]
