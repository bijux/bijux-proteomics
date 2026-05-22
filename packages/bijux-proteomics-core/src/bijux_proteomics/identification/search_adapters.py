# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Search-engine adapter contracts over normalized PSM parsing."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification import (
    CalibrationPlotData,
    FdrAuditTrail,
    PsmParseReport,
    PsmRecord,
    SearchResultProvenanceManifest,
    SearchResultValidationIssue,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    normalize_psm_records,
    normalize_psm_score_orientation,
    parse_psm_tsv,
    select_best_psm_per_spectrum,
)
from bijux_proteomics.identification import (
    SearchResultColumnMapping as SearchResultColumnMapping,
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


_COMET_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.COMET,
    display_name="Comet",
    description="Normalize Comet-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.LOWER_BETTER,
    score_family=SearchScoreFamily.EXPECTATION_VALUE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan",
        "plain_peptide",
        "charge",
        "expect",
        "protein",
        "target_decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan",
        peptide="plain_peptide",
        charge="charge",
        score="expect",
        protein_refs="protein",
        decoy_label="target_decoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("decoy", "true", "1"),
        explicit_target_values=("target", "false", "0"),
    ),
    supported_extensions=(".txt", ".tsv"),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=True,
)

_MSFRAGGER_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    display_name="MSFragger",
    description="Normalize MSFragger-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.HYPERSCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "Spectrum",
        "Peptide",
        "Charge",
        "Hyperscore",
        "Protein",
        "IsDecoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="Spectrum",
        peptide="Peptide",
        charge="Charge",
        score="Hyperscore",
        protein_refs="Protein",
        decoy_label="IsDecoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("1", "decoy", "true"),
        explicit_target_values=("0", "target", "false"),
    ),
    supported_extensions=(".tsv",),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=True,
)

_SAGE_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    display_name="Sage",
    description="Normalize Sage-like tabular search outputs into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.DISCRIMINANT_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scannr",
        "peptide",
        "charge",
        "discriminant_score",
        "proteins",
        "label",
        "q_value",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scannr",
        peptide="peptide",
        charge="charge",
        score="discriminant_score",
        protein_refs="proteins",
        q_value="q_value",
        decoy_label="label",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("decoy", "-1", "1"),
        explicit_target_values=("target", "1", "0"),
    ),
    supported_extensions=(".tsv",),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=True,
)

_MAXQUANT_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    display_name="MaxQuant evidence",
    description="Normalize MaxQuant evidence-like tables into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.ENGINE_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "MS/MS scan number",
        "Modified sequence",
        "Charge",
        "Score",
        "Proteins",
        "Reverse",
        "PEP",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="MS/MS scan number",
        peptide="Modified sequence",
        charge="Charge",
        score="Score",
        protein_refs="Proteins",
        q_value="PEP",
        decoy_label="Reverse",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="REV__",
        explicit_decoy_values=("+", "decoy", "true", "1"),
        explicit_target_values=("", "target", "false", "0"),
    ),
    supported_extensions=(".txt", ".tsv"),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=False,
)

_DIANN_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.DIANN,
    display_name="DIA-NN",
    description="Normalize DIA-NN report-style tables into stable PSM-like records.",
    score_orientation=ScoreOrientation.LOWER_BETTER,
    score_family=SearchScoreFamily.Q_VALUE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "Precursor.Id",
        "Stripped.Sequence",
        "Precursor.Charge",
        "Q.Value",
        "Protein.Ids",
        "Decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="Precursor.Id",
        peptide="Stripped.Sequence",
        charge="Precursor.Charge",
        score="Q.Value",
        protein_refs="Protein.Ids",
        q_value="Q.Value",
        decoy_label="Decoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("1", "true", "decoy"),
        explicit_target_values=("0", "false", "target"),
    ),
    supported_extensions=(".tsv",),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=False,
)

_SPECTRONAUT_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    display_name="Spectronaut",
    description="Normalize Spectronaut-like tables into stable PSM-like records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    score_family=SearchScoreFamily.CONFIDENCE_SCORE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "EG.PrecursorId",
        "PEP.StrippedSequence",
        "FG.Charge",
        "EG.Cscore",
        "PG.ProteinAccessions",
        "EG.IsDecoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="EG.PrecursorId",
        peptide="PEP.StrippedSequence",
        charge="FG.Charge",
        score="EG.Cscore",
        protein_refs="PG.ProteinAccessions",
        decoy_label="EG.IsDecoy",
        protein_separator=";",
    ),
    default_decoy_policy=TargetDecoyLabelPolicy(
        protein_prefix="DECOY_",
        explicit_decoy_values=("true", "1", "decoy"),
        explicit_target_values=("false", "0", "target"),
    ),
    supported_extensions=(".tsv",),
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_external_execution=False,
)

_GENERIC_MANIFEST = SearchAdapterManifest(
    adapter_kind=SearchAdapterKind.GENERIC,
    display_name="Generic search table",
    description="Normalize a user-mapped generic search-result table into stable PSM records.",
    score_orientation=ScoreOrientation.HIGHER_BETTER,
    native_columns=(),
    mapping=None,
    default_decoy_policy=TargetDecoyLabelPolicy(),
    supported_extensions=(".tsv", ".txt"),
    supports_q_value=True,
    supports_explicit_decoy_label=True,
    supports_protein_refs=True,
    supports_config_hash=True,
    supports_external_execution=False,
)


_COMET_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.COMET,
    dialect_id="pipeline-export",
    display_name="Comet pipeline export",
    description="Normalize a Comet-like pipeline export with renamed expectation columns.",
    score_family=SearchScoreFamily.EXPECTATION_VALUE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan_num",
        "peptide_sequence",
        "precursor_charge",
        "expectation_value",
        "protein_ids",
        "is_decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan_num",
        peptide="peptide_sequence",
        charge="precursor_charge",
        score="expectation_value",
        protein_refs="protein_ids",
        decoy_label="is_decoy",
        protein_separator=";",
    ),
)

_COMET_PSM_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.COMET,
    dialect_id="comet-psm",
    display_name="Comet psm export",
    description="Normalize a realistic Comet tabular export into stable PSM records.",
    score_family=SearchScoreFamily.EXPECTATION_VALUE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan",
        "plain_peptide",
        "modified_peptide",
        "charge",
        "expect",
        "xcorr",
        "delta_cn",
        "sp_score",
        "protein",
        "target_decoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan",
        peptide="plain_peptide",
        charge="charge",
        score="expect",
        protein_refs="protein",
        decoy_label="target_decoy",
        protein_separator=";",
    ),
)

_MSFRAGGER_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    dialect_id="pipeline-export",
    display_name="MSFragger pipeline export",
    description="Normalize an MSFragger-like pipeline export with renamed hyperscore fields.",
    score_family=SearchScoreFamily.HYPERSCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "spectrum_key",
        "plain_peptide",
        "precursor_charge",
        "hyperscore_value",
        "proteins_joined",
        "decoy_state",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="spectrum_key",
        peptide="plain_peptide",
        charge="precursor_charge",
        score="hyperscore_value",
        protein_refs="proteins_joined",
        decoy_label="decoy_state",
        protein_separator=";",
    ),
)

_FRAGPIPE_PSM_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MSFRAGGER,
    dialect_id="fragpipe-psm",
    display_name="FragPipe psm export",
    description="Normalize a FragPipe psm.tsv export into stable PSM records.",
    score_family=SearchScoreFamily.HYPERSCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "Spectrum",
        "Spectrum File",
        "Peptide",
        "Modified Peptide",
        "Charge",
        "Hyperscore",
        "Intensity",
        "Protein",
        "IsDecoy",
        "QValue",
        "Assigned Modifications",
        "Observed Modifications",
        "Mass Difference",
    ),
    mapping=SearchResultColumnMapping(
        run_id="Spectrum File",
        spectrum_id="Spectrum",
        peptide="Peptide",
        charge="Charge",
        score="Hyperscore",
        intensity="Intensity",
        protein_refs="Protein",
        q_value="QValue",
        decoy_label="IsDecoy",
        protein_separator=";",
    ),
)

_SAGE_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    dialect_id="pipeline-export",
    display_name="Sage pipeline export",
    description="Normalize a Sage-like pipeline export with renamed score fields.",
    score_family=SearchScoreFamily.DISCRIMINANT_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan_id",
        "stripped_peptide",
        "precursor_charge",
        "score_discriminant",
        "protein_group",
        "decoy_flag",
        "qvalue",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan_id",
        peptide="stripped_peptide",
        charge="precursor_charge",
        score="score_discriminant",
        protein_refs="protein_group",
        q_value="qvalue",
        decoy_label="decoy_flag",
        protein_separator=";",
    ),
)

_SAGE_PSM_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SAGE,
    dialect_id="sage-psm",
    display_name="Sage psm export",
    description="Normalize a realistic Sage PSM export into stable PSM records.",
    score_family=SearchScoreFamily.DISCRIMINANT_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "filename",
        "scannr",
        "peptide",
        "charge",
        "discriminant_score",
        "hyperscore",
        "proteins",
        "label",
        "q_value",
        "peptide_q_value",
        "protein_q_value",
        "posterior_error",
        "matched_peaks",
        "longest_b",
        "longest_y",
        "matched_intensity_pct",
        "precursor_ppm",
        "fragment_ppm",
        "isotope_error",
        "rt",
        "aligned_rt",
        "predicted_rt",
        "delta_rt_model",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scannr",
        peptide="peptide",
        charge="charge",
        score="discriminant_score",
        protein_refs="proteins",
        q_value="q_value",
        decoy_label="label",
        protein_separator=";",
    ),
)

_MAXQUANT_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    dialect_id="pipeline-export",
    display_name="MaxQuant pipeline export",
    description="Normalize a MaxQuant-like pipeline export with simplified evidence columns.",
    score_family=SearchScoreFamily.ENGINE_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "scan_number",
        "sequence_with_mods",
        "precursor_charge",
        "score_value",
        "leading_proteins",
        "reverse_flag",
        "pep_value",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="scan_number",
        peptide="sequence_with_mods",
        charge="precursor_charge",
        score="score_value",
        protein_refs="leading_proteins",
        q_value="pep_value",
        decoy_label="reverse_flag",
        protein_separator=";",
    ),
)

_MAXQUANT_BUNDLE_EVIDENCE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
    dialect_id="bundle-evidence",
    display_name="MaxQuant bundle evidence",
    description="Normalize a native MaxQuant evidence table by stripped sequence while preserving modified notation in the raw row.",
    score_family=SearchScoreFamily.ENGINE_SCORE,
    result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
    native_columns=(
        "MS/MS scan number",
        "Sequence",
        "Modified sequence",
        "Charge",
        "Score",
        "Proteins",
        "Reverse",
        "PEP",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="MS/MS scan number",
        peptide="Sequence",
        charge="Charge",
        score="Score",
        protein_refs="Proteins",
        q_value="PEP",
        decoy_label="Reverse",
        protein_separator=";",
    ),
)

_DIANN_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.DIANN,
    dialect_id="pipeline-export",
    display_name="DIA-NN pipeline export",
    description="Normalize a DIA-NN-like pipeline export with simplified report columns.",
    score_family=SearchScoreFamily.Q_VALUE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "precursor_id",
        "sequence",
        "charge",
        "qvalue",
        "protein_ids",
        "decoy_flag",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="precursor_id",
        peptide="sequence",
        charge="charge",
        score="qvalue",
        protein_refs="protein_ids",
        q_value="qvalue",
        decoy_label="decoy_flag",
        protein_separator=";",
    ),
)

_SPECTRONAUT_PIPELINE_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    dialect_id="pipeline-export",
    display_name="Spectronaut pipeline export",
    description="Normalize a Spectronaut-like pipeline export with simplified precursor columns.",
    score_family=SearchScoreFamily.CONFIDENCE_SCORE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "precursor_key",
        "stripped_sequence",
        "charge",
        "cscore_value",
        "protein_accessions",
        "decoy_flag",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="precursor_key",
        peptide="stripped_sequence",
        charge="charge",
        score="cscore_value",
        protein_refs="protein_accessions",
        decoy_label="decoy_flag",
        protein_separator=";",
    ),
)

_SPECTRONAUT_REVIEW_REPORT_DIALECT = SearchAdapterDialectManifest(
    adapter_kind=SearchAdapterKind.SPECTRONAUT,
    dialect_id="review-report",
    display_name="Spectronaut review report",
    description="Normalize a Spectronaut export that preserves q-value alongside the confidence score.",
    score_family=SearchScoreFamily.CONFIDENCE_SCORE,
    result_family=SearchResultFamily.MIXED_TARGET_LIBRARY,
    native_columns=(
        "EG.PrecursorId",
        "PEP.StrippedSequence",
        "FG.LabeledSequence",
        "FG.Charge",
        "EG.Cscore",
        "EG.Qvalue",
        "PG.ProteinGroups",
        "PG.ProteinAccessions",
        "R.FileName",
        "R.Condition",
        "FG.Quantity",
        "PG.Quantity",
        "EG.IsDecoy",
    ),
    mapping=SearchResultColumnMapping(
        spectrum_id="EG.PrecursorId",
        peptide="PEP.StrippedSequence",
        charge="FG.Charge",
        score="EG.Cscore",
        protein_refs="PG.ProteinAccessions",
        q_value="EG.Qvalue",
        decoy_label="EG.IsDecoy",
        protein_separator=";",
    ),
)


def _default_dialect_from_manifest(
    manifest: SearchAdapterManifest,
) -> SearchAdapterDialectManifest | None:
    if manifest.mapping is None:
        return None
    return SearchAdapterDialectManifest(
        adapter_kind=manifest.adapter_kind,
        dialect_id="default",
        display_name=manifest.display_name,
        description=manifest.description,
        score_family=manifest.score_family,
        result_family=manifest.result_family,
        native_columns=manifest.native_columns,
        mapping=manifest.mapping,
    )


def search_adapter_registry() -> dict[SearchAdapterKind, SearchAdapterManifest]:
    """Return the built-in search adapter registry."""
    manifests = (
        _COMET_MANIFEST,
        _MSFRAGGER_MANIFEST,
        _SAGE_MANIFEST,
        _MAXQUANT_MANIFEST,
        _DIANN_MANIFEST,
        _SPECTRONAUT_MANIFEST,
        _GENERIC_MANIFEST,
    )
    return {manifest.adapter_kind: manifest for manifest in manifests}


def search_adapter_dialect_registry() -> dict[
    tuple[SearchAdapterKind, str], SearchAdapterDialectManifest
]:
    """Return the built-in search adapter dialect registry."""
    dialects = [
        dialect
        for dialect in (
            _default_dialect_from_manifest(manifest)
            for manifest in search_adapter_registry().values()
        )
        if dialect is not None
    ]
    dialects.extend(
        [
            _COMET_PIPELINE_DIALECT,
            _COMET_PSM_DIALECT,
            _MSFRAGGER_PIPELINE_DIALECT,
            _FRAGPIPE_PSM_DIALECT,
            _SAGE_PSM_DIALECT,
            _SAGE_PIPELINE_DIALECT,
            _MAXQUANT_PIPELINE_DIALECT,
            _MAXQUANT_BUNDLE_EVIDENCE_DIALECT,
            _DIANN_PIPELINE_DIALECT,
            _SPECTRONAUT_PIPELINE_DIALECT,
            _SPECTRONAUT_REVIEW_REPORT_DIALECT,
        ]
    )
    return {(dialect.adapter_kind, dialect.dialect_id): dialect for dialect in dialects}


def get_search_adapter_manifest(
    adapter_kind: SearchAdapterKind,
) -> SearchAdapterManifest:
    """Fetch one built-in adapter manifest."""
    return search_adapter_registry()[adapter_kind]


def _resolve_search_adapter_dialect(
    *,
    adapter_kind: SearchAdapterKind,
    dialect_id: str,
    additional_dialects: tuple[SearchAdapterDialectManifest, ...],
) -> SearchAdapterDialectManifest | None:
    built_in = search_adapter_dialect_registry()
    extensions = {
        (dialect.adapter_kind, dialect.dialect_id): dialect
        for dialect in additional_dialects
    }
    if len(extensions) != len(additional_dialects):
        raise ValueError("additional adapter dialects must not contain duplicates")
    key = (adapter_kind, dialect_id)
    dialect = extensions.get(key) or built_in.get(key)
    if dialect is None:
        if adapter_kind is SearchAdapterKind.GENERIC and dialect_id == "default":
            return None
        raise ValueError(
            f"search adapter dialect {dialect_id!r} is not registered for {adapter_kind.value!r}"
        )
    return dialect


def _manifest_for_dialect(
    *,
    adapter_kind: SearchAdapterKind,
    dialect: SearchAdapterDialectManifest | None,
) -> SearchAdapterManifest:
    manifest = get_search_adapter_manifest(adapter_kind)
    if dialect is None:
        return manifest
    return manifest.model_copy(
        update={
            "description": dialect.description,
            "display_name": dialect.display_name,
            "score_family": dialect.score_family,
            "result_family": dialect.result_family,
            "native_columns": dialect.native_columns,
            "mapping": dialect.mapping,
        }
    )


def build_search_adapter_capability_matrix() -> tuple[SearchAdapterCapability, ...]:
    """Build a stable capability matrix over built-in search adapters."""
    rows = [
        SearchAdapterCapability(
            adapter_kind=manifest.adapter_kind,
            display_name=manifest.display_name,
            score_orientation=manifest.score_orientation,
            score_family=manifest.score_family,
            result_family=manifest.result_family,
            supports_q_value=manifest.supports_q_value,
            supports_explicit_decoy_label=manifest.supports_explicit_decoy_label,
            supports_protein_refs=manifest.supports_protein_refs,
            supports_config_hash=manifest.supports_config_hash,
            supports_external_execution=manifest.supports_external_execution,
            native_columns=manifest.native_columns,
        )
        for manifest in search_adapter_registry().values()
    ]
    return tuple(sorted(rows, key=lambda row: row.adapter_kind.value))


def _score_families_compatible(
    left: SearchScoreFamily,
    right: SearchScoreFamily,
) -> tuple[bool, str]:
    if left is right:
        return True, f"both reports use the same score family {left.value}"
    if SearchScoreFamily.GENERIC_NUMERIC in {left, right}:
        return (
            True,
            "one report uses generic numeric scores, so normalized ranking is comparable but native semantics remain partially unspecified",
        )
    return (
        False,
        f"score families {left.value} and {right.value} are orientation-normalizable but not natively interchangeable",
    )


def build_search_result_family_policy(
    manifest: SearchAdapterManifest,
) -> SearchResultFamilyPolicy:
    """Build the explicit policy for one adapter result family."""
    if manifest.result_family is SearchResultFamily.DATABASE_TARGET_DECOY:
        return SearchResultFamilyPolicy(
            result_family=manifest.result_family,
            requires_target_decoy_evidence=True,
            requires_protein_references=manifest.supports_protein_refs,
            allows_library_style_scores=False,
            note="database target-decoy search results should preserve decoy evidence and protein references when the engine provides them",
        )
    if manifest.result_family is SearchResultFamily.LIBRARY_SEARCH:
        return SearchResultFamilyPolicy(
            result_family=manifest.result_family,
            requires_target_decoy_evidence=False,
            requires_protein_references=manifest.supports_protein_refs,
            allows_library_style_scores=True,
            note="library search results may rank by spectral-library confidence without explicit target-decoy evidence on every row",
        )
    return SearchResultFamilyPolicy(
        result_family=manifest.result_family,
        requires_target_decoy_evidence=False,
        requires_protein_references=manifest.supports_protein_refs,
        allows_library_style_scores=True,
        note="mixed target and library search results must keep their hybrid family explicit so downstream review does not assume pure database semantics",
    )


def _hash_file(path: Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_search_result_rows(
    path: Path,
) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("search result TSV must include a header row")
        source_columns = tuple(
            str(column) for column in reader.fieldnames if column is not None
        )
        for row in reader:
            if None in row:
                raise ValueError(
                    "search result TSV contains rows with inconsistent column counts"
                )
            rows.append(
                {str(key): str(value) for key, value in row.items() if key is not None}
            )
    return source_columns, tuple(rows)


def _mapped_column_names(mapping: SearchResultColumnMapping) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            column_name
            for column_name in (
                mapping.run_id,
                mapping.spectrum_id,
                mapping.peptide,
                mapping.modified_peptide,
                mapping.charge,
                mapping.score,
                mapping.intensity,
                mapping.q_value,
                mapping.protein_refs,
                mapping.decoy_label,
                mapping.contaminant_label,
            )
            if column_name is not None
        )
    )


def _mapped_field_values(
    row: dict[str, str],
    mapping: SearchResultColumnMapping,
) -> dict[str, str]:
    values: dict[str, str] = {}
    for role_name, column_name in (
        ("run_id", mapping.run_id),
        ("spectrum_id", mapping.spectrum_id),
        ("peptide", mapping.peptide),
        ("modified_peptide", mapping.modified_peptide),
        ("charge", mapping.charge),
        ("score", mapping.score),
        ("intensity", mapping.intensity),
        ("q_value", mapping.q_value),
        ("protein_refs", mapping.protein_refs),
        ("decoy_label", mapping.decoy_label),
        ("contaminant_label", mapping.contaminant_label),
    ):
        if column_name is None or column_name not in row:
            continue
        values[role_name] = row[column_name]
    return values


def _build_evidence_rows(
    *,
    source_rows: tuple[dict[str, str], ...],
    parse_report: PsmParseReport,
) -> tuple[SearchNormalizedEvidenceEntry, ...]:
    rejected_by_row_number = {
        rejected.row_number: rejected for rejected in parse_report.rejected_rows
    }
    accepted_index = 0
    mapped_columns = set(_mapped_column_names(parse_report.column_mapping))
    entries: list[SearchNormalizedEvidenceEntry] = []
    for row_index, raw_fields in enumerate(source_rows, start=2):
        rejected = rejected_by_row_number.get(row_index)
        if rejected is not None:
            entries.append(
                SearchNormalizedEvidenceEntry(
                    row_number=row_index,
                    accepted=False,
                    raw_fields=raw_fields,
                    mapped_field_values=_mapped_field_values(
                        raw_fields,
                        parse_report.column_mapping,
                    ),
                    unmapped_native_fields={
                        key: value
                        for key, value in raw_fields.items()
                        if key not in mapped_columns
                    },
                    normalized_record=None,
                    issues=rejected.issues,
                )
            )
            continue
        record = parse_report.accepted_records[accepted_index]
        accepted_index += 1
        entries.append(
            SearchNormalizedEvidenceEntry(
                row_number=row_index,
                accepted=True,
                raw_fields=raw_fields,
                mapped_field_values=_mapped_field_values(
                    raw_fields,
                    parse_report.column_mapping,
                ),
                unmapped_native_fields={
                    key: value
                    for key, value in raw_fields.items()
                    if key not in mapped_columns
                },
                normalized_record=record,
                issues=(),
            )
        )
    return tuple(entries)


def _required_mapping_columns(mapping: SearchResultColumnMapping) -> tuple[str, ...]:
    return (
        mapping.spectrum_id,
        mapping.peptide,
        mapping.charge,
        mapping.score,
    )


def _mapped_field_roles(mapping: SearchResultColumnMapping) -> dict[str, str]:
    return {
        role_name: column_name
        for role_name, column_name in (
            ("spectrum_id", mapping.spectrum_id),
            ("peptide", mapping.peptide),
            ("charge", mapping.charge),
            ("score", mapping.score),
            ("q_value", mapping.q_value),
            ("protein_refs", mapping.protein_refs),
            ("decoy_label", mapping.decoy_label),
        )
        if column_name is not None
    }


def assess_search_result_input(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    dialect_id: str = "default",
    mapping: SearchResultColumnMapping | None = None,
    additional_dialects: tuple[SearchAdapterDialectManifest, ...] = (),
) -> SearchInputAssessmentReport:
    """Assess whether a search input is sufficiently specified and compatible."""
    refusals: list[SearchInputRefusal] = []
    source_columns: tuple[str, ...] = ()
    row_count = 0
    try:
        dialect = _resolve_search_adapter_dialect(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            additional_dialects=additional_dialects,
        )
    except ValueError as exc:
        return SearchInputAssessmentReport(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            valid=False,
            source_columns=(),
            row_count=0,
            refusals=(
                SearchInputRefusal(
                    kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                    code="unknown_adapter_dialect",
                    message=str(exc),
                    remediation_hint="register the adapter dialect explicitly or use a built-in dialect identifier",
                ),
            ),
        )
    manifest = _manifest_for_dialect(adapter_kind=adapter_kind, dialect=dialect)
    resolved_mapping = (
        mapping or (None if dialect is None else dialect.mapping) or manifest.mapping
    )
    if resolved_mapping is None:
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                code="missing_column_mapping",
                message="generic adapter input requires an explicit column mapping",
                remediation_hint="provide a SearchResultColumnMapping for the generic input table",
            )
        )
        return SearchInputAssessmentReport(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            valid=False,
            source_columns=(),
            row_count=0,
            refusals=tuple(refusals),
        )
    try:
        source_columns, source_rows = _read_search_result_rows(source_path)
        row_count = len(source_rows)
    except ValueError as exc:
        return SearchInputAssessmentReport(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            valid=False,
            source_columns=(),
            row_count=0,
            refusals=(
                SearchInputRefusal(
                    kind=SearchInputRefusalKind.MALFORMED_INPUT,
                    code="malformed_search_table",
                    message=str(exc),
                    remediation_hint="provide a tab-delimited search table with a valid header row",
                ),
            ),
        )
    if row_count == 0:
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                code="empty_search_table",
                message="search result table does not contain any data rows",
                remediation_hint="provide at least one search-result row for normalization",
            )
        )
    missing_required = sorted(
        column
        for column in _required_mapping_columns(resolved_mapping)
        if column not in source_columns
    )
    if missing_required:
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                code="missing_required_columns",
                message=f"missing required search-result columns: {', '.join(missing_required)}",
                remediation_hint="align the mapping and input header so spectrum, peptide, charge, and score columns are present",
            )
        )
    family_policy = build_search_result_family_policy(manifest)
    if family_policy.requires_target_decoy_evidence and (
        resolved_mapping.decoy_label is None
        and resolved_mapping.protein_refs is None
        and not manifest.default_decoy_policy.protein_prefix
        and not manifest.default_decoy_policy.protein_suffix
    ):
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.SCIENTIFIC_INCOMPATIBILITY,
                code="missing_target_decoy_evidence",
                message="database target-decoy normalization requires explicit decoy evidence or protein references that support decoy inference",
                remediation_hint="provide a decoy label column or protein references with a decoy naming policy",
            )
        )
    if (
        family_policy.requires_protein_references
        and resolved_mapping.protein_refs is None
    ):
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.SCIENTIFIC_INCOMPATIBILITY,
                code="missing_protein_references",
                message="this adapter family expects protein references for downstream protein-level review",
                remediation_hint="map or export the engine protein-reference column before normalization",
            )
        )
    return SearchInputAssessmentReport(
        adapter_kind=adapter_kind,
        dialect_id=dialect_id,
        valid=not refusals,
        source_columns=source_columns,
        row_count=row_count,
        refusals=tuple(refusals),
    )


def build_search_adapter_field_accounting(
    normalization_report: SearchAdapterNormalizationReport,
) -> SearchAdapterFieldAccounting:
    """Summarize mapped, preserved, unsupported, and lost adapter fields."""
    mapping = normalization_report.parse_report.column_mapping
    mapped_columns = set(_mapped_column_names(mapping))
    source_columns = set(normalization_report.source_columns)
    supported_columns = (
        set(normalization_report.adapter_manifest.native_columns) or mapped_columns
    )
    return SearchAdapterFieldAccounting(
        source_columns=tuple(normalization_report.source_columns),
        mapped_columns=tuple(sorted(source_columns & mapped_columns)),
        preserved_native_only_columns=tuple(
            sorted((source_columns & supported_columns) - mapped_columns)
        ),
        unsupported_columns=tuple(sorted(source_columns - supported_columns)),
        lost_columns=tuple(sorted(supported_columns - source_columns)),
        mapped_field_roles=_mapped_field_roles(mapping),
    )


_SUPPORTED_ENZYMES = {
    "trypsin",
    "trypsin/p",
    "lys-c",
    "lys-n",
    "arg-c",
    "asp-n",
    "glu-c",
    "chymotrypsin",
    "no_enzyme",
    "unspecific",
}

_COMET_ENZYME_BY_NUMBER = {
    "0": "no_enzyme",
    "1": "trypsin",
    "2": "trypsin/p",
    "3": "lys-c",
    "4": "lys-n",
    "5": "arg-c",
    "6": "asp-n",
    "8": "glu-c",
}


def _parse_key_value_parameters(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key.strip()] = value.strip()
    return fields


def _fixed_modifications_from_fields(
    fields: dict[str, str],
) -> tuple[SearchModificationDefinition, ...]:
    definitions: list[SearchModificationDefinition] = []
    for key, value in sorted(fields.items()):
        if not key.startswith("add_"):
            continue
        residue_tokens = key.split("_")
        if len(residue_tokens) < 2:
            continue
        site = residue_tokens[1][:1].upper()
        try:
            mass_delta = float(value)
        except ValueError:
            continue
        if mass_delta == 0.0:
            continue
        definitions.append(
            SearchModificationDefinition(
                site=site,
                mass_delta=mass_delta,
                variable=False,
                source_key=key,
            )
        )
    return tuple(definitions)


def _variable_modifications_from_key_value_fields(
    fields: dict[str, str],
) -> tuple[SearchModificationDefinition, ...]:
    definitions: list[SearchModificationDefinition] = []
    for key, value in sorted(fields.items()):
        if not key.startswith("variable_mod"):
            continue
        tokens = value.split()
        if len(tokens) < 2:
            continue
        try:
            mass_delta = float(tokens[0])
        except ValueError:
            continue
        site = tokens[1].upper()
        definitions.append(
            SearchModificationDefinition(
                site=site,
                mass_delta=mass_delta,
                variable=True,
                source_key=key,
            )
        )
    return tuple(definitions)


def _parse_comet_parameters(path: Path) -> SearchParameterReport:
    fields = _parse_key_value_parameters(path)
    precursor_units = (
        SearchToleranceUnit.PPM
        if fields.get("peptide_mass_units") == "2"
        else SearchToleranceUnit.DA
    )
    enzyme = _COMET_ENZYME_BY_NUMBER.get(
        fields.get("search_enzyme_number", "").strip(),
        fields.get("search_enzyme_name", "unknown").strip().lower(),
    )
    database_path = fields.get("database_name")
    decoy_search = fields.get("decoy_search", "0").strip() in {"1", "true", "yes"}
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.COMET,
        adapter_name="Comet",
        enzyme=enzyme,
        missed_cleavages=int(fields["allowed_missed_cleavage"])
        if fields.get("allowed_missed_cleavage")
        else None,
        precursor_tolerance=float(fields["peptide_mass_tolerance"])
        if fields.get("peptide_mass_tolerance")
        else None,
        precursor_tolerance_unit=precursor_units,
        fragment_tolerance=float(fields["fragment_bin_tol"])
        if fields.get("fragment_bin_tol")
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.DA
        if fields.get("fragment_bin_tol")
        else None,
        database_path=database_path,
        decoy_prefix="DECOY_" if decoy_search else None,
        has_decoy_strategy=decoy_search
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=_fixed_modifications_from_fields(fields),
        variable_modifications=_variable_modifications_from_key_value_fields(fields),
        raw_fields=fields,
    )


def _parse_msfragger_parameters(path: Path) -> SearchParameterReport:
    fields = _parse_key_value_parameters(path)
    precursor_unit = (
        SearchToleranceUnit.PPM
        if fields.get("precursor_mass_units") == "1"
        else SearchToleranceUnit.DA
    )
    fragment_unit = (
        SearchToleranceUnit.PPM
        if fields.get("fragment_mass_units") == "1"
        else SearchToleranceUnit.DA
    )
    lower = (
        abs(float(fields["precursor_mass_lower"]))
        if fields.get("precursor_mass_lower")
        else None
    )
    upper = (
        abs(float(fields["precursor_mass_upper"]))
        if fields.get("precursor_mass_upper")
        else None
    )
    precursor_tolerance = (
        max(lower or 0.0, upper or 0.0)
        if lower is not None or upper is not None
        else None
    )
    database_path = fields.get("database_name")
    decoy_prefix = fields.get("decoy_prefix")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        adapter_name="MSFragger",
        enzyme=fields.get("search_enzyme_name", "unknown").strip().lower(),
        missed_cleavages=int(fields["allowed_missed_cleavage"])
        if fields.get("allowed_missed_cleavage")
        else None,
        precursor_tolerance=precursor_tolerance,
        precursor_tolerance_unit=precursor_unit
        if precursor_tolerance is not None
        else None,
        fragment_tolerance=float(fields["fragment_mass_tolerance"])
        if fields.get("fragment_mass_tolerance")
        else None,
        fragment_tolerance_unit=fragment_unit
        if fields.get("fragment_mass_tolerance")
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=_fixed_modifications_from_fields(fields),
        variable_modifications=_variable_modifications_from_key_value_fields(fields),
        raw_fields=fields,
    )


def _parse_sage_parameters(path: Path) -> SearchParameterReport:
    payload = json.loads(path.read_text())
    enzyme_payload = payload.get("enzyme", {})
    database_payload = payload.get("database", {})
    precursor_payload = payload.get("precursor_tol", {})
    fragment_payload = payload.get("fragment_tol", {})
    mods_payload = payload.get("mods", {})

    enzyme_name = (
        str(enzyme_payload).strip().lower()
        if isinstance(enzyme_payload, str)
        else str(enzyme_payload.get("name", "unknown")).strip().lower()
    )
    missed_cleavages = (
        payload.get("missed_cleavages")
        if isinstance(enzyme_payload, str)
        else enzyme_payload.get("missed_cleavages")
    )
    precursor_value = None
    precursor_unit = None
    if isinstance(precursor_payload, dict) and precursor_payload:
        precursor_unit = (
            SearchToleranceUnit.PPM
            if "ppm" in precursor_payload
            else SearchToleranceUnit.DA
            if "da" in precursor_payload
            else None
        )
        precursor_value = precursor_payload.get("ppm", precursor_payload.get("da"))
    elif payload.get("precursor_tol_ppm") is not None:
        precursor_unit = SearchToleranceUnit.PPM
        precursor_value = payload.get("precursor_tol_ppm")
    elif payload.get("precursor_tol_da") is not None:
        precursor_unit = SearchToleranceUnit.DA
        precursor_value = payload.get("precursor_tol_da")

    fragment_value = None
    fragment_unit = None
    if isinstance(fragment_payload, dict) and fragment_payload:
        fragment_unit = (
            SearchToleranceUnit.PPM
            if "ppm" in fragment_payload
            else SearchToleranceUnit.DA
            if "da" in fragment_payload
            else None
        )
        fragment_value = fragment_payload.get("ppm", fragment_payload.get("da"))
    elif payload.get("fragment_tol_ppm") is not None:
        fragment_unit = SearchToleranceUnit.PPM
        fragment_value = payload.get("fragment_tol_ppm")
    elif payload.get("fragment_tol_da") is not None:
        fragment_unit = SearchToleranceUnit.DA
        fragment_value = payload.get("fragment_tol_da")

    def _mass_delta_for_named_modification(name: str) -> float:
        known = {
            "acetyl": 42.010565,
            "carbamidomethyl": 57.021464,
            "oxidation": 15.994915,
            "phospho": 79.966331,
        }
        return known.get(name.strip().lower(), 0.0)

    def _compact_sage_modifications(
        values: object,
        *,
        variable: bool,
        prefix: str,
    ) -> tuple[SearchModificationDefinition, ...]:
        if not isinstance(values, list):
            return ()
        definitions: list[SearchModificationDefinition] = []
        for token in values:
            if not isinstance(token, str) or "@" not in token:
                continue
            name, residues = token.split("@", 1)
            mass_delta = _mass_delta_for_named_modification(name)
            for residue in residues:
                definitions.append(
                    SearchModificationDefinition(
                        site=residue.upper(),
                        mass_delta=mass_delta,
                        variable=variable,
                        source_key=f"{prefix}.{name}@{residue.upper()}",
                    )
                )
        return tuple(definitions)

    fixed_definitions = tuple(
        SearchModificationDefinition(
            site=str(site).upper(),
            mass_delta=float(mass_delta),
            variable=False,
            source_key=f"mods.static.{site}",
        )
        for site, mass_delta in sorted(
            (mods_payload.get("static") or {}).items()
            if isinstance(mods_payload, dict)
            else {}
        )
    )
    variable_definitions = tuple(
        SearchModificationDefinition(
            site=str(site).upper(),
            mass_delta=float(mass_delta),
            variable=True,
            source_key=f"mods.variable.{site}",
        )
        for site, deltas in sorted(
            (mods_payload.get("variable") or {}).items()
            if isinstance(mods_payload, dict)
            else {}
        )
        for mass_delta in deltas
    )
    if not fixed_definitions:
        fixed_definitions = _compact_sage_modifications(
            payload.get("fixed_modifications"),
            variable=False,
            prefix="fixed_modifications",
        )
    if not variable_definitions:
        variable_definitions = _compact_sage_modifications(
            payload.get("variable_modifications"),
            variable=True,
            prefix="variable_modifications",
        )
    database_path = (
        database_payload.get("fasta")
        if isinstance(database_payload, dict)
        else payload.get("database_path")
    )
    decoy_prefix = (
        database_payload.get("decoy_tag")
        if isinstance(database_payload, dict)
        else payload.get("decoy_prefix")
    )
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.SAGE,
        adapter_name="Sage",
        enzyme=enzyme_name,
        missed_cleavages=int(missed_cleavages)
        if missed_cleavages is not None
        else None,
        precursor_tolerance=float(precursor_value)
        if precursor_unit is not None and precursor_value is not None
        else None,
        precursor_tolerance_unit=precursor_unit,
        fragment_tolerance=float(fragment_value)
        if fragment_unit is not None and fragment_value is not None
        else None,
        fragment_tolerance_unit=fragment_unit,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_definitions,
        variable_modifications=variable_definitions,
        raw_fields={
            key: json.dumps(value, sort_keys=True)
            for key, value in sorted(payload.items())
        },
    )


def _modification_definitions_from_compact_value(
    value: str | None,
    *,
    variable: bool,
    source_key: str,
) -> tuple[SearchModificationDefinition, ...]:
    if not value:
        return ()
    definitions: list[SearchModificationDefinition] = []
    for token in value.split(";"):
        entry = token.strip()
        if not entry or ":" not in entry:
            continue
        site, delta = entry.split(":", 1)
        site_clean = site.strip().upper()
        if not site_clean:
            continue
        try:
            mass_delta = float(delta.strip())
        except ValueError:
            continue
        definitions.append(
            SearchModificationDefinition(
                site=site_clean,
                mass_delta=mass_delta,
                variable=variable,
                source_key=f"{source_key}.{site_clean}",
            )
        )
    return tuple(definitions)


def _parse_maxquant_parameters(path: Path) -> SearchParameterReport:
    fields = _parse_key_value_parameters(path)
    fixed_modifications = _modification_definitions_from_compact_value(
        fields.get("fixed_modifications"),
        variable=False,
        source_key="fixed_modifications",
    )
    variable_modifications = _modification_definitions_from_compact_value(
        fields.get("variable_modifications"),
        variable=True,
        source_key="variable_modifications",
    )
    database_path = fields.get("fasta_file")
    decoy_prefix = fields.get("decoy_prefix", "REV__").strip() or None
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        adapter_name="MaxQuant evidence",
        enzyme=fields.get("enzyme", "unknown").strip().lower(),
        missed_cleavages=int(fields["max_missed_cleavages"])
        if fields.get("max_missed_cleavages")
        else None,
        precursor_tolerance=float(fields["precursor_tolerance_ppm"])
        if fields.get("precursor_tolerance_ppm")
        else None,
        precursor_tolerance_unit=SearchToleranceUnit.PPM
        if fields.get("precursor_tolerance_ppm")
        else None,
        fragment_tolerance=float(fields["fragment_tolerance_da"])
        if fields.get("fragment_tolerance_da")
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.DA
        if fields.get("fragment_tolerance_da")
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications,
        variable_modifications=variable_modifications,
        raw_fields=fields,
    )


def _parse_diann_parameters(path: Path) -> SearchParameterReport:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("dia-nn parameter payload must be a JSON object")
    fixed_modifications = _modification_definitions_from_compact_value(
        str(payload.get("fixed_modifications", "")),
        variable=False,
        source_key="fixed_modifications",
    )
    variable_modifications = _modification_definitions_from_compact_value(
        str(payload.get("variable_modifications", "")),
        variable=True,
        source_key="variable_modifications",
    )
    database_path = (
        str(payload.get("fasta_file", "")).strip()
        or str(payload.get("library_file", "")).strip()
        or None
    )
    decoy_prefix = str(payload.get("decoy_prefix", "")).strip() or None
    precursor_value = payload.get("precursor_tolerance_ppm")
    fragment_value = payload.get("fragment_tolerance_ppm")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.DIANN,
        adapter_name="DIA-NN",
        enzyme=str(payload.get("enzyme", "unspecific")).strip().lower(),
        missed_cleavages=int(payload["max_missed_cleavages"])
        if payload.get("max_missed_cleavages") is not None
        else None,
        precursor_tolerance=float(precursor_value)
        if precursor_value is not None
        else None,
        precursor_tolerance_unit=SearchToleranceUnit.PPM
        if precursor_value is not None
        else None,
        fragment_tolerance=float(fragment_value)
        if fragment_value is not None
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.PPM
        if fragment_value is not None
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications,
        variable_modifications=variable_modifications,
        raw_fields={
            key: json.dumps(value, sort_keys=True)
            for key, value in sorted(payload.items())
        },
    )


def _parse_spectronaut_parameters(path: Path) -> SearchParameterReport:
    fields = _parse_key_value_parameters(path)
    fixed_modifications = _modification_definitions_from_compact_value(
        fields.get("fixed_modifications"),
        variable=False,
        source_key="fixed_modifications",
    )
    variable_modifications = _modification_definitions_from_compact_value(
        fields.get("variable_modifications"),
        variable=True,
        source_key="variable_modifications",
    )
    database_path = fields.get("library_file") or fields.get("fasta_file") or None
    decoy_prefix = fields.get("decoy_prefix")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
        adapter_name="Spectronaut",
        enzyme=fields.get("digestion_enzyme", "unknown").strip().lower(),
        missed_cleavages=int(fields["max_missed_cleavages"])
        if fields.get("max_missed_cleavages")
        else None,
        precursor_tolerance=float(fields["precursor_tolerance_ppm"])
        if fields.get("precursor_tolerance_ppm")
        else None,
        precursor_tolerance_unit=SearchToleranceUnit.PPM
        if fields.get("precursor_tolerance_ppm")
        else None,
        fragment_tolerance=float(fields["fragment_tolerance_ppm"])
        if fields.get("fragment_tolerance_ppm")
        else None,
        fragment_tolerance_unit=SearchToleranceUnit.PPM
        if fields.get("fragment_tolerance_ppm")
        else None,
        database_path=database_path,
        decoy_prefix=decoy_prefix,
        has_decoy_strategy=bool(decoy_prefix)
        or bool(database_path and "decoy" in database_path.lower()),
        fixed_modifications=fixed_modifications,
        variable_modifications=variable_modifications,
        raw_fields=fields,
    )


def parse_search_parameter_file(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
) -> SearchParameterReport:
    """Parse one supported search-engine parameter file into a stable contract."""
    if adapter_kind is SearchAdapterKind.COMET:
        return _parse_comet_parameters(source_path)
    if adapter_kind is SearchAdapterKind.MSFRAGGER:
        return _parse_msfragger_parameters(source_path)
    if adapter_kind is SearchAdapterKind.SAGE:
        return _parse_sage_parameters(source_path)
    if adapter_kind is SearchAdapterKind.MAXQUANT_EVIDENCE:
        return _parse_maxquant_parameters(source_path)
    if adapter_kind is SearchAdapterKind.DIANN:
        return _parse_diann_parameters(source_path)
    if adapter_kind is SearchAdapterKind.SPECTRONAUT:
        return _parse_spectronaut_parameters(source_path)
    raise ValueError(
        f"search parameter parsing is not supported for adapter {adapter_kind.value!r}"
    )


def _supports_search_parameter_parsing(adapter_kind: SearchAdapterKind) -> bool:
    return adapter_kind in {
        SearchAdapterKind.COMET,
        SearchAdapterKind.MSFRAGGER,
        SearchAdapterKind.SAGE,
        SearchAdapterKind.MAXQUANT_EVIDENCE,
        SearchAdapterKind.DIANN,
        SearchAdapterKind.SPECTRONAUT,
    }


def validate_search_parameters(
    parameters: SearchParameterReport,
) -> SearchConfigValidationReport:
    """Validate one parsed search-engine configuration."""
    issues: list[SearchConfigValidationIssue] = []
    if parameters.enzyme not in _SUPPORTED_ENZYMES:
        issues.append(
            SearchConfigValidationIssue(
                code="unknown_enzyme",
                message=f"unsupported enzyme {parameters.enzyme!r}",
                severity="error",
            )
        )
    if not parameters.database_path:
        issues.append(
            SearchConfigValidationIssue(
                code="missing_database_path",
                message="search configuration must declare a database path",
                severity="error",
            )
        )
    if not parameters.has_decoy_strategy:
        issues.append(
            SearchConfigValidationIssue(
                code="missing_decoy_strategy",
                message="search configuration does not declare a decoy prefix or decoy database",
                severity="error",
            )
        )
    if parameters.precursor_tolerance is None or parameters.precursor_tolerance <= 0:
        issues.append(
            SearchConfigValidationIssue(
                code="invalid_precursor_tolerance",
                message="precursor tolerance must be positive",
                severity="error",
            )
        )
    if parameters.fragment_tolerance is None or parameters.fragment_tolerance <= 0:
        issues.append(
            SearchConfigValidationIssue(
                code="invalid_fragment_tolerance",
                message="fragment tolerance must be positive",
                severity="error",
            )
        )
    fixed_by_signature = {
        (definition.site, round(definition.mass_delta, 6))
        for definition in parameters.fixed_modifications
    }
    for definition in parameters.variable_modifications:
        signature = (definition.site, round(definition.mass_delta, 6))
        if signature in fixed_by_signature:
            issues.append(
                SearchConfigValidationIssue(
                    code="overlapping_modification_definition",
                    message=(
                        f"modification {definition.site}@{definition.mass_delta} is both fixed and variable"
                    ),
                    severity="error",
                )
            )
    return SearchConfigValidationReport(
        parameters=parameters,
        valid=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )


def _render_parameter_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, tuple):
        return json.dumps(
            [item.to_dict() if hasattr(item, "to_dict") else item for item in value],
            sort_keys=True,
            separators=(",", ":"),
        )
    return str(value)


def compare_search_parameters(
    left: SearchParameterReport,
    right: SearchParameterReport,
) -> SearchParameterComparisonReport:
    """Compare normalized engine parameter reports across runs or engines."""
    comparable = (
        left.adapter_kind is right.adapter_kind
        and left.enzyme == right.enzyme
        and left.precursor_tolerance_unit == right.precursor_tolerance_unit
        and left.fragment_tolerance_unit == right.fragment_tolerance_unit
    )
    differences: list[SearchParameterDifferenceEntry] = []
    for field_name, left_value, right_value, note in (
        (
            "enzyme",
            left.enzyme,
            right.enzyme,
            "digestion enzyme differences alter the search space and are not directly interchangeable",
        ),
        (
            "missed_cleavages",
            left.missed_cleavages,
            right.missed_cleavages,
            "missed-cleavage policy changes the enumerated peptide space",
        ),
        (
            "precursor_tolerance",
            left.precursor_tolerance,
            right.precursor_tolerance,
            "precursor tolerance differences change precursor matching strictness",
        ),
        (
            "precursor_tolerance_unit",
            left.precursor_tolerance_unit,
            right.precursor_tolerance_unit,
            "precursor tolerance units must be aligned before comparing parameter strictness",
        ),
        (
            "fragment_tolerance",
            left.fragment_tolerance,
            right.fragment_tolerance,
            "fragment tolerance differences change fragment matching strictness",
        ),
        (
            "fragment_tolerance_unit",
            left.fragment_tolerance_unit,
            right.fragment_tolerance_unit,
            "fragment tolerance units must be aligned before comparing parameter strictness",
        ),
        (
            "database_path",
            left.database_path,
            right.database_path,
            "database path differences may indicate distinct search databases",
        ),
        (
            "decoy_prefix",
            left.decoy_prefix,
            right.decoy_prefix,
            "decoy-prefix differences change decoy interpretation and downstream FDR expectations",
        ),
        (
            "fixed_modifications",
            left.fixed_modifications,
            right.fixed_modifications,
            "fixed modification differences change the assumed peptide masses",
        ),
        (
            "variable_modifications",
            left.variable_modifications,
            right.variable_modifications,
            "variable modification differences change the allowed search hypotheses",
        ),
    ):
        rendered_left = _render_parameter_value(left_value)
        rendered_right = _render_parameter_value(right_value)
        differences.append(
            SearchParameterDifferenceEntry(
                field_name=field_name,
                left_value=rendered_left,
                right_value=rendered_right,
                severity="compatible"
                if rendered_left == rendered_right
                else "different",
                note=note,
            )
        )
    return SearchParameterComparisonReport(
        left_adapter_kind=left.adapter_kind,
        right_adapter_kind=right.adapter_kind,
        left_adapter_name=left.adapter_name,
        right_adapter_name=right.adapter_name,
        comparable=comparable,
        differences=tuple(differences),
    )


def _build_parse_provenance(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    adapter_manifest: SearchAdapterManifest,
) -> SearchResultProvenanceManifest:
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=_hash_file(source_path),
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=adapter_manifest.default_decoy_policy,
        fdr_policy=None,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def normalize_search_results_with_adapter(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    dialect_id: str = "default",
    mapping: SearchResultColumnMapping | None = None,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    additional_dialects: tuple[SearchAdapterDialectManifest, ...] = (),
) -> SearchAdapterNormalizationReport:
    """Normalize one search table with a built-in or user-supplied adapter mapping."""
    dialect = _resolve_search_adapter_dialect(
        adapter_kind=adapter_kind,
        dialect_id=dialect_id,
        additional_dialects=additional_dialects,
    )
    manifest = _manifest_for_dialect(adapter_kind=adapter_kind, dialect=dialect)
    resolved_mapping = (
        mapping or (None if dialect is None else dialect.mapping) or manifest.mapping
    )
    if resolved_mapping is None:
        raise ValueError(
            "generic adapter normalization requires an explicit column mapping"
        )
    source_columns, source_rows = _read_search_result_rows(source_path)
    parse_report = parse_psm_tsv(
        source_path,
        mapping=resolved_mapping,
        decoy_policy=decoy_policy or manifest.default_decoy_policy,
    )
    return SearchAdapterNormalizationReport(
        adapter_manifest=manifest,
        family_policy=build_search_result_family_policy(manifest),
        source_columns=source_columns,
        parse_report=parse_report,
        normalized_records=normalize_psm_records(parse_report.accepted_records),
        evidence_rows=_build_evidence_rows(
            source_rows=source_rows,
            parse_report=parse_report,
        ),
    )


def compare_search_result_reports(
    left: SearchAdapterNormalizationReport,
    right: SearchAdapterNormalizationReport,
) -> SearchResultComparabilityReport:
    """Compare two normalized search-result reports on a shared score scale."""
    score_family_compatible, score_family_note = _score_families_compatible(
        left.adapter_manifest.score_family,
        right.adapter_manifest.score_family,
    )
    left_by_spectrum = {
        record.spectrum_id: record
        for record in normalize_psm_records(left.normalized_records)
    }
    right_by_spectrum = {
        record.spectrum_id: record
        for record in normalize_psm_records(right.normalized_records)
    }
    shared_spectra = sorted(set(left_by_spectrum) & set(right_by_spectrum))
    left_only = set(left_by_spectrum) - set(right_by_spectrum)
    right_only = set(right_by_spectrum) - set(left_by_spectrum)
    left_normalized = {
        (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
        for entry in normalize_psm_score_orientation(
            left.normalized_records,
            score_orientation=left.adapter_manifest.score_orientation.value,
        )
    }
    right_normalized = {
        (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
        for entry in normalize_psm_score_orientation(
            right.normalized_records,
            score_orientation=right.adapter_manifest.score_orientation.value,
        )
    }
    exact_match_count = 0
    label_conflict_count = 0
    shared_peptides: set[str] = set()
    total_score_delta = 0.0
    for spectrum_id in shared_spectra:
        left_record = left_by_spectrum[spectrum_id]
        right_record = right_by_spectrum[spectrum_id]
        shared_peptides.add(left_record.canonical_peptide)
        shared_peptides.add(right_record.canonical_peptide)
        if (
            left_record.canonical_peptide == right_record.canonical_peptide
            and left_record.charge == right_record.charge
        ):
            exact_match_count += 1
        if left_record.target_decoy_label is not right_record.target_decoy_label:
            label_conflict_count += 1
        left_score = left_normalized.get(
            (left_record.spectrum_id, left_record.canonical_peptide), 0.0
        )
        right_score = right_normalized.get(
            (right_record.spectrum_id, right_record.canonical_peptide), 0.0
        )
        total_score_delta += abs(left_score - right_score)
    shared_count = len(shared_spectra)
    return SearchResultComparabilityReport(
        left_adapter_kind=left.adapter_manifest.adapter_kind,
        right_adapter_kind=right.adapter_manifest.adapter_kind,
        left_score_family=left.adapter_manifest.score_family,
        right_score_family=right.adapter_manifest.score_family,
        left_result_family=left.adapter_manifest.result_family,
        right_result_family=right.adapter_manifest.result_family,
        score_family_compatible=score_family_compatible,
        score_family_note=score_family_note,
        left_total_psms=len(left.normalized_records),
        right_total_psms=len(right.normalized_records),
        shared_spectrum_count=shared_count,
        left_only_spectrum_count=len(left_only),
        right_only_spectrum_count=len(right_only),
        shared_peptide_count=len(shared_peptides),
        exact_match_count=exact_match_count,
        label_conflict_count=label_conflict_count,
        peptide_agreement_fraction=exact_match_count / shared_count
        if shared_count
        else 0.0,
        mean_normalized_score_delta=total_score_delta / shared_count
        if shared_count
        else 0.0,
    )


def merge_search_result_reports(
    reports: tuple[SearchAdapterNormalizationReport, ...],
) -> SearchResultMergeReport:
    """Merge multiple engine reports without flattening engine-specific uncertainty."""
    if not reports:
        return SearchResultMergeReport(
            adapter_kinds=(),
            merged_entries=(),
            exact_agreement_count=0,
            conflict_count=0,
            partial_coverage_count=0,
        )
    adapter_kinds = tuple(report.adapter_manifest.adapter_kind for report in reports)
    if len(set(adapter_kinds)) != len(adapter_kinds):
        raise ValueError("multi-engine merge requires distinct adapter kinds")

    normalized_scores_by_adapter: dict[
        SearchAdapterKind, dict[tuple[str, str], float]
    ] = {}
    per_report_best: list[
        tuple[SearchAdapterNormalizationReport, dict[str, PsmRecord]]
    ] = []
    for report in reports:
        normalized_scores_by_adapter[report.adapter_manifest.adapter_kind] = {
            (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
            for entry in normalize_psm_score_orientation(
                report.normalized_records,
                score_orientation=report.adapter_manifest.score_orientation.value,
            )
        }
        best = {
            record.spectrum_id: record
            for record in select_best_psm_per_spectrum(report.normalized_records)
        }
        per_report_best.append((report, best))

    all_spectra = sorted(
        {spectrum_id for _, best in per_report_best for spectrum_id in best}
    )
    merged_entries: list[MergedSearchSpectrumEntry] = []
    for spectrum_id in all_spectra:
        observations: list[SearchEngineObservation] = []
        for report, best in per_report_best:
            record = best.get(spectrum_id)
            if record is None:
                continue
            observations.append(
                SearchEngineObservation(
                    adapter_kind=report.adapter_manifest.adapter_kind,
                    adapter_name=report.adapter_manifest.display_name,
                    score_family=report.adapter_manifest.score_family,
                    result_family=report.adapter_manifest.result_family,
                    normalized_score=normalized_scores_by_adapter[
                        report.adapter_manifest.adapter_kind
                    ].get((record.spectrum_id, record.canonical_peptide), 0.0),
                    q_value=record.q_value,
                    record=record,
                )
            )
        peptide_set = {entry.record.canonical_peptide for entry in observations}
        charge_set = {entry.record.charge for entry in observations}
        label_set = {entry.record.target_decoy_label for entry in observations}
        if len(observations) < len(reports):
            status = SearchMergeAgreementStatus.PARTIAL_COVERAGE
            note = "not every engine produced an accepted observation for this spectrum"
        elif len(peptide_set) > 1:
            status = SearchMergeAgreementStatus.PEPTIDE_CONFLICT
            note = "engines disagree on the peptide assignment for this spectrum"
        elif len(charge_set) > 1:
            status = SearchMergeAgreementStatus.CHARGE_CONFLICT
            note = "engines agree on the peptide but disagree on precursor charge"
        elif len(label_set) > 1:
            status = SearchMergeAgreementStatus.LABEL_CONFLICT
            note = (
                "engines disagree on the target-decoy interpretation for this spectrum"
            )
        else:
            status = SearchMergeAgreementStatus.EXACT_MATCH
            note = "all engines agree on peptide, charge, and target-decoy label"
        merged_entries.append(
            MergedSearchSpectrumEntry(
                spectrum_id=spectrum_id,
                observations=tuple(
                    sorted(observations, key=lambda entry: entry.adapter_kind.value)
                ),
                agreement_status=status,
                consensus_peptide=observations[0].record.canonical_peptide
                if len(peptide_set) == 1
                else None,
                consensus_charge=observations[0].record.charge
                if len(charge_set) == 1
                else None,
                uncertainty_note=note,
            )
        )
    return SearchResultMergeReport(
        adapter_kinds=tuple(sorted(adapter_kinds, key=lambda kind: kind.value)),
        merged_entries=tuple(merged_entries),
        exact_agreement_count=sum(
            entry.agreement_status is SearchMergeAgreementStatus.EXACT_MATCH
            for entry in merged_entries
        ),
        conflict_count=sum(
            entry.agreement_status
            in {
                SearchMergeAgreementStatus.PEPTIDE_CONFLICT,
                SearchMergeAgreementStatus.CHARGE_CONFLICT,
                SearchMergeAgreementStatus.LABEL_CONFLICT,
            }
            for entry in merged_entries
        ),
        partial_coverage_count=sum(
            entry.agreement_status is SearchMergeAgreementStatus.PARTIAL_COVERAGE
            for entry in merged_entries
        ),
    )


def _peptide_definition_style(
    records: tuple[PsmRecord, ...],
) -> str:
    if any(
        any(marker in record.canonical_peptide for marker in ("[", "]", "(", ")", "."))
        for record in records
    ):
        return "modified_or_annotated"
    return "stripped_sequence"


def assess_search_merge_compatibility(
    reports: tuple[SearchAdapterNormalizationReport, ...],
) -> SearchMergeCompatibilityReport:
    """Assess whether reports are compatible for mixed-engine evidence merging."""
    adapter_kinds = tuple(report.adapter_manifest.adapter_kind for report in reports)
    issues: list[SearchMergeCompatibilityIssue] = []
    if len(set(adapter_kinds)) != len(adapter_kinds):
        issues.append(
            SearchMergeCompatibilityIssue(
                code="duplicate_adapter_kind",
                message="mixed-engine merge requires distinct adapter kinds",
                severity="error",
                adapter_kinds=adapter_kinds,
            )
        )
    result_families = {report.adapter_manifest.result_family for report in reports}
    if len(result_families) > 1:
        issues.append(
            SearchMergeCompatibilityIssue(
                code="result_family_mismatch",
                message="mixed-engine merge requires a single compatible result family",
                severity="error",
                adapter_kinds=adapter_kinds,
            )
        )

    for left_index, left in enumerate(reports):
        for right in reports[left_index + 1 :]:
            compatible, note = _score_families_compatible(
                left.adapter_manifest.score_family,
                right.adapter_manifest.score_family,
            )
            if not compatible:
                issues.append(
                    SearchMergeCompatibilityIssue(
                        code="score_family_mismatch",
                        message=note,
                        severity="error",
                        adapter_kinds=(
                            left.adapter_manifest.adapter_kind,
                            right.adapter_manifest.adapter_kind,
                        ),
                    )
                )
            left_policy = left.adapter_manifest.default_decoy_policy
            right_policy = right.adapter_manifest.default_decoy_policy
            left_signature = (
                left_policy.protein_prefix,
                left_policy.protein_suffix,
                tuple(left_policy.explicit_decoy_values),
                tuple(left_policy.explicit_target_values),
            )
            right_signature = (
                right_policy.protein_prefix,
                right_policy.protein_suffix,
                tuple(right_policy.explicit_decoy_values),
                tuple(right_policy.explicit_target_values),
            )
            if (
                left_signature != right_signature
                and all(
                    bool(signature[0] or signature[1] or signature[2] or signature[3])
                    for signature in (left_signature, right_signature)
                )
                and SearchAdapterKind.GENERIC
                not in {
                    left.adapter_manifest.adapter_kind,
                    right.adapter_manifest.adapter_kind,
                }
            ):
                issues.append(
                    SearchMergeCompatibilityIssue(
                        code="decoy_policy_mismatch",
                        message="engine decoy policies differ and may produce non-comparable target-decoy interpretation",
                        severity="error",
                        adapter_kinds=(
                            left.adapter_manifest.adapter_kind,
                            right.adapter_manifest.adapter_kind,
                        ),
                    )
                )

    peptide_styles = {
        report.adapter_manifest.adapter_kind: _peptide_definition_style(
            report.normalized_records
        )
        for report in reports
    }
    if len(set(peptide_styles.values())) > 1:
        issues.append(
            SearchMergeCompatibilityIssue(
                code="peptide_definition_mismatch",
                message="engine peptide definitions differ between stripped and modified sequence representations",
                severity="error",
                adapter_kinds=tuple(
                    sorted(peptide_styles.keys(), key=lambda kind: kind.value)
                ),
            )
        )

    return SearchMergeCompatibilityReport(
        adapter_kinds=tuple(sorted(adapter_kinds, key=lambda kind: kind.value)),
        compatible=not any(issue.severity == "error" for issue in issues),
        issues=tuple(issues),
    )


def merge_search_result_reports_with_compatibility(
    reports: tuple[SearchAdapterNormalizationReport, ...],
) -> SearchResultMergeReport:
    """Merge reports only when compatibility checks succeed."""
    compatibility = assess_search_merge_compatibility(reports)
    if not compatibility.compatible:
        rendered = "; ".join(
            f"{issue.code}: {issue.message}" for issue in compatibility.issues
        )
        raise ValueError(
            f"multi-engine merge refused due to compatibility errors: {rendered}"
        )
    return merge_search_result_reports(reports)


def build_external_engine_disagreement_report(
    reports: tuple[SearchAdapterNormalizationReport, ...],
    *,
    confidence_delta_threshold: float = 0.35,
) -> ExternalEngineDisagreementReport:
    """Build disagreement diagnostics across external engine outputs."""
    if not reports:
        return ExternalEngineDisagreementReport(
            adapter_kinds=(),
            entries=(),
            disagreement_counts={},
        )
    per_report_best: list[
        tuple[SearchAdapterNormalizationReport, dict[str, PsmRecord]]
    ] = []
    normalized_scores: dict[SearchAdapterKind, dict[tuple[str, str], float]] = {}
    for report in reports:
        best = {
            record.spectrum_id: record
            for record in select_best_psm_per_spectrum(report.normalized_records)
        }
        per_report_best.append((report, best))
        normalized_scores[report.adapter_manifest.adapter_kind] = {
            (entry.spectrum_id, entry.canonical_peptide): entry.normalized_score
            for entry in normalize_psm_score_orientation(
                report.normalized_records,
                score_orientation=report.adapter_manifest.score_orientation.value,
            )
        }
    all_spectrum_ids = sorted(
        {spectrum_id for _, best in per_report_best for spectrum_id in best}
    )
    entries: list[ExternalEngineDisagreementEntry] = []
    for spectrum_id in all_spectrum_ids:
        observations: list[tuple[SearchAdapterKind, PsmRecord, float]] = []
        for report, best in per_report_best:
            record = best.get(spectrum_id)
            if record is None:
                continue
            adapter_kind = report.adapter_manifest.adapter_kind
            observations.append(
                (
                    adapter_kind,
                    record,
                    normalized_scores[adapter_kind].get(
                        (record.spectrum_id, record.canonical_peptide), 0.0
                    ),
                )
            )
        if len(observations) < len(reports):
            missing_kinds = tuple(
                sorted(
                    {
                        report.adapter_manifest.adapter_kind
                        for report, best in per_report_best
                        if spectrum_id not in best
                    },
                    key=lambda kind: kind.value,
                )
            )
            present_kinds = tuple(
                sorted(
                    {entry[0] for entry in observations},
                    key=lambda kind: kind.value,
                )
            )
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.MISSING_EVIDENCE,
                    adapter_kinds=tuple(
                        sorted(
                            set(missing_kinds + present_kinds),
                            key=lambda kind: kind.value,
                        )
                    ),
                    message="at least one engine is missing accepted evidence for this spectrum id",
                    normalized_score_delta=None,
                )
            )
        if len(observations) < 2:
            continue
        peptides = {entry[1].canonical_peptide for entry in observations}
        charges = {entry[1].charge for entry in observations}
        labels = {entry[1].target_decoy_label for entry in observations}
        adapter_kinds = tuple(
            sorted({entry[0] for entry in observations}, key=lambda kind: kind.value)
        )
        if len(peptides) > 1:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.PEPTIDE_CONFLICT,
                    adapter_kinds=adapter_kinds,
                    message="engines disagree on the accepted peptide assignment",
                    normalized_score_delta=None,
                )
            )
        if len(charges) > 1:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.CHARGE_CONFLICT,
                    adapter_kinds=adapter_kinds,
                    message="engines disagree on precursor charge assignment",
                    normalized_score_delta=None,
                )
            )
        if len(labels) > 1:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.LABEL_CONFLICT,
                    adapter_kinds=adapter_kinds,
                    message="engines disagree on target-decoy interpretation",
                    normalized_score_delta=None,
                )
            )
        score_values = [entry[2] for entry in observations]
        score_delta = max(score_values) - min(score_values)
        if score_delta >= confidence_delta_threshold:
            entries.append(
                ExternalEngineDisagreementEntry(
                    spectrum_id=spectrum_id,
                    kind=ExternalEngineDisagreementKind.CONFIDENCE_GAP,
                    adapter_kinds=adapter_kinds,
                    message="engine confidence differs materially after orientation normalization",
                    normalized_score_delta=score_delta,
                )
            )
    disagreement_counts: dict[str, int] = {}
    for entry in entries:
        disagreement_counts[entry.kind.value] = (
            disagreement_counts.get(entry.kind.value, 0) + 1
        )
    return ExternalEngineDisagreementReport(
        adapter_kinds=tuple(
            sorted(
                {report.adapter_manifest.adapter_kind for report in reports},
                key=lambda kind: kind.value,
            )
        ),
        entries=tuple(entries),
        disagreement_counts=dict(sorted(disagreement_counts.items())),
    )


def _fixture_adapter_kind(path: Path) -> SearchAdapterKind | None:
    stem = path.stem.lower()
    if "comet" in stem:
        return SearchAdapterKind.COMET
    if "msfragger" in stem:
        return SearchAdapterKind.MSFRAGGER
    if "sage" in stem:
        return SearchAdapterKind.SAGE
    if "maxquant" in stem:
        return SearchAdapterKind.MAXQUANT_EVIDENCE
    if "diann" in stem:
        return SearchAdapterKind.DIANN
    if "spectronaut" in stem:
        return SearchAdapterKind.SPECTRONAUT
    if "generic" in stem:
        return SearchAdapterKind.GENERIC
    return None


def _fixture_kind_for_path(path: Path) -> tuple[SearchRegressionFixtureKind, str]:
    suffix = path.suffix.lower()
    stem = path.stem.lower()
    if "malformed" in stem or "invalid" in stem:
        return (
            SearchRegressionFixtureKind.FAILURE_CASE,
            "fixture captures malformed or scientifically invalid search inputs",
        )
    if suffix == ".json" and "mapping" in stem:
        return (
            SearchRegressionFixtureKind.MAPPING_CONTROL,
            "fixture defines explicit mapping control state for generic normalization",
        )
    if stem.endswith("pipeline_export"):
        return (
            SearchRegressionFixtureKind.PIPELINE_EXPORT,
            "fixture captures a richer pipeline-style engine export surface",
        )
    if suffix in {".params", ".json"}:
        return (
            SearchRegressionFixtureKind.PARAMETER_FILE,
            "fixture captures engine parameter provenance and validation state",
        )
    if suffix in {".tsv", ".txt"} and (
        "results" in stem
        or "report" in stem
        or "evidence" in stem
        or stem.endswith("_merge")
    ):
        return (
            SearchRegressionFixtureKind.ENGINE_EXPORT_LIKE,
            "fixture captures an engine-style result export for regression coverage",
        )
    return (
        SearchRegressionFixtureKind.OTHER,
        "fixture supports auxiliary regression coverage outside the main export classes",
    )


def build_search_adapter_regression_corpus_manifest(
    corpus_root: Path,
) -> SearchRegressionCorpusManifest:
    """Build a stable manifest over a directory of search adapter regression fixtures."""
    entries: list[SearchRegressionCorpusEntry] = []
    for path in sorted(
        candidate for candidate in corpus_root.rglob("*") if candidate.is_file()
    ):
        fixture_kind, note = _fixture_kind_for_path(path)
        entries.append(
            SearchRegressionCorpusEntry(
                relative_path=str(path.relative_to(corpus_root)),
                sha256=_hash_file(path) or "",
                adapter_kind=_fixture_adapter_kind(path),
                fixture_kind=fixture_kind,
                note=note,
            )
        )
    covered_adapter_kinds = tuple(
        sorted(
            {entry.adapter_kind for entry in entries if entry.adapter_kind is not None},
            key=lambda kind: kind.value,
        )
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_adapter_regression_corpus_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchRegressionCorpusManifest(
        document_schema=schema,
        corpus_root=str(corpus_root),
        entries=tuple(entries),
        covered_adapter_kinds=covered_adapter_kinds,
        engine_export_like_count=sum(
            entry.fixture_kind is SearchRegressionFixtureKind.ENGINE_EXPORT_LIKE
            for entry in entries
        ),
        failure_case_count=sum(
            entry.fixture_kind is SearchRegressionFixtureKind.FAILURE_CASE
            for entry in entries
        ),
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def build_search_adapter_conformance_report(
    normalization_report: SearchAdapterNormalizationReport,
) -> SearchAdapterConformanceReport:
    """Build a stable conformance report over one adapter normalization run."""
    manifest = normalization_report.adapter_manifest
    field_accounting = build_search_adapter_field_accounting(normalization_report)
    rejection_issue_counts: dict[str, int] = {}
    for rejected in normalization_report.parse_report.rejected_rows:
        for issue in rejected.issues:
            rejection_issue_counts[issue.code] = (
                rejection_issue_counts.get(issue.code, 0) + 1
            )

    checks = [
        SearchAdapterConformanceCheck(
            code="stable_normalized_order",
            passed=normalization_report.normalized_records
            == normalize_psm_records(normalization_report.normalized_records),
            detail="normalized output order matches the shared stable PSM ordering",
        ),
        SearchAdapterConformanceCheck(
            code="q_value_contract",
            passed=(
                not manifest.supports_q_value
                or all(
                    record.q_value is not None
                    for record in normalization_report.normalized_records
                )
            ),
            detail="q-value-supporting adapters must emit q-values for accepted records",
        ),
        SearchAdapterConformanceCheck(
            code="explicit_decoy_contract",
            passed=(
                not manifest.supports_explicit_decoy_label
                or all(
                    record.target_decoy_label is not TargetDecoyLabel.UNKNOWN
                    for record in normalization_report.normalized_records
                )
            ),
            detail="explicit-decoy adapters must not leave accepted rows with unknown labels",
        ),
        SearchAdapterConformanceCheck(
            code="protein_reference_contract",
            passed=(
                not manifest.supports_protein_refs
                or all(
                    record.protein_refs
                    for record in normalization_report.normalized_records
                )
            ),
            detail="protein-aware adapters must emit at least one protein reference per accepted row",
        ),
        SearchAdapterConformanceCheck(
            code="rejected_invalid_score_rows",
            passed=rejection_issue_counts.get("invalid_score", 0) == 0,
            detail="adapter input should not contain invalid score rows for conformance-grade fixtures",
        ),
        SearchAdapterConformanceCheck(
            code="rejected_invalid_q_value_rows",
            passed=rejection_issue_counts.get("invalid_q_value", 0) == 0,
            detail="adapter input should not contain invalid q-value rows for conformance-grade fixtures",
        ),
        SearchAdapterConformanceCheck(
            code="expected_native_fields_present",
            passed=not field_accounting.lost_columns,
            detail="adapter-declared native columns should be present in conformance-grade source tables",
        ),
    ]
    fdr_audit_trail = build_fdr_audit_trail(
        normalization_report.normalized_records,
        score_orientation=manifest.score_orientation.value,
    )
    calibration_plot = build_calibration_plot_data(
        normalization_report.normalized_records,
        score_orientation=manifest.score_orientation.value,
    )
    return SearchAdapterConformanceReport(
        adapter_kind=manifest.adapter_kind,
        accepted_rows=len(normalization_report.parse_report.accepted_records),
        rejected_rows=len(normalization_report.parse_report.rejected_rows),
        rejection_issue_counts=dict(sorted(rejection_issue_counts.items())),
        field_accounting=field_accounting,
        checks=tuple(checks),
        passes=all(check.passed for check in checks),
        fdr_audit_trail=fdr_audit_trail,
        calibration_plot=calibration_plot,
    )


def build_search_adapter_provenance_manifest(
    *,
    source_path: Path,
    normalization_report: SearchAdapterNormalizationReport,
    adapter_version: str | None = None,
    config_path: Path | None = None,
) -> SearchAdapterProvenanceManifest:
    """Build provenance for one adapter normalization pass."""
    parameter_report = (
        parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=normalization_report.adapter_manifest.adapter_kind,
        )
        if config_path is not None
        and _supports_search_parameter_parsing(
            normalization_report.adapter_manifest.adapter_kind
        )
        else None
    )
    parse_provenance = _build_parse_provenance(
        source_path=source_path,
        parse_report=normalization_report.parse_report,
        adapter_manifest=normalization_report.adapter_manifest,
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_adapter_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchAdapterProvenanceManifest(
        document_schema=schema,
        adapter_kind=normalization_report.adapter_manifest.adapter_kind,
        adapter_name=normalization_report.adapter_manifest.display_name,
        adapter_version=adapter_version,
        source_path=str(source_path),
        source_sha256=_hash_file(source_path) or "",
        config_path=str(config_path) if config_path is not None else None,
        config_sha256=_hash_file(config_path),
        parameter_report=parameter_report,
        result_family=normalization_report.adapter_manifest.result_family,
        family_policy=normalization_report.family_policy,
        native_columns=normalization_report.adapter_manifest.native_columns,
        score_orientation=normalization_report.adapter_manifest.score_orientation,
        parse_provenance=parse_provenance,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


class SearchCorpusInputSpecification(JsonModel):
    """One declared search-result input inside an adapter corpus."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    dialect_id: str = Field(..., min_length=1)
    result_file: str = Field(..., min_length=1)
    config_file: str | None = None


class SearchCorpusNormalizationEntry(JsonModel):
    """One normalized corpus input with conformance and provenance summaries."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    dialect_id: str = Field(..., min_length=1)
    result_path: str = Field(..., min_length=1)
    config_path: str | None = None
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    conformance_passes: bool
    mapped_columns: tuple[str, ...] = Field(default_factory=tuple)
    preserved_native_only_columns: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_columns: tuple[str, ...] = Field(default_factory=tuple)
    lost_columns: tuple[str, ...] = Field(default_factory=tuple)
    source_sha256: str = Field(..., min_length=64, max_length=64)
    config_sha256: str | None = None


class SearchEngineCorpusReport(JsonModel):
    """Corpus-level normalization coverage for one search adapter family."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    corpus_root: str = Field(..., min_length=1)
    entries: tuple[SearchCorpusNormalizationEntry, ...] = Field(default_factory=tuple)
    missing_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    total_accepted_rows: int = Field(..., ge=0)
    total_rejected_rows: int = Field(..., ge=0)
    passes: bool
    note: str = Field(..., min_length=1)


class SearchAdapterCorpusConformanceEntry(JsonModel):
    """Conformance summary row for one adapter corpus report."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    corpus_root: str = Field(..., min_length=1)
    corpus_passes: bool
    corpus_entry_count: int = Field(..., ge=0)
    total_accepted_rows: int = Field(..., ge=0)
    total_rejected_rows: int = Field(..., ge=0)
    unsupported_column_count: int = Field(..., ge=0)
    lost_column_count: int = Field(..., ge=0)


class SearchAdapterCorpusConformanceMatrix(JsonModel):
    """Conformance matrix across all built-in engine corpora."""

    model_config = ConfigDict(extra="forbid")

    matrix_root: str = Field(..., min_length=1)
    entries: tuple[SearchAdapterCorpusConformanceEntry, ...] = Field(
        default_factory=tuple
    )
    passes: bool


def build_search_engine_corpus_report(
    *,
    corpus_root: Path,
    adapter_kind: SearchAdapterKind,
    input_specs: tuple[SearchCorpusInputSpecification, ...],
) -> SearchEngineCorpusReport:
    """Build a corpus coverage report for one adapter from declared fixture inputs."""
    if not input_specs:
        raise ValueError("at least one corpus input specification is required")
    if any(spec.adapter_kind is not adapter_kind for spec in input_specs):
        raise ValueError("all corpus input specifications must match the adapter kind")

    entries: list[SearchCorpusNormalizationEntry] = []
    missing_artifacts: list[str] = []
    for spec in input_specs:
        result_path = corpus_root / spec.result_file
        config_path = corpus_root / spec.config_file if spec.config_file else None
        if not result_path.exists():
            missing_artifacts.append(str(result_path.relative_to(corpus_root)))
            continue
        if config_path is not None and not config_path.exists():
            missing_artifacts.append(str(config_path.relative_to(corpus_root)))
            continue

        normalization = normalize_search_results_with_adapter(
            source_path=result_path,
            adapter_kind=adapter_kind,
            dialect_id=spec.dialect_id,
        )
        conformance = build_search_adapter_conformance_report(normalization)
        provenance = build_search_adapter_provenance_manifest(
            source_path=result_path,
            normalization_report=normalization,
            config_path=config_path,
        )
        field_accounting = conformance.field_accounting
        entries.append(
            SearchCorpusNormalizationEntry(
                adapter_kind=adapter_kind,
                dialect_id=spec.dialect_id,
                result_path=str(result_path),
                config_path=str(config_path) if config_path is not None else None,
                accepted_rows=conformance.accepted_rows,
                rejected_rows=conformance.rejected_rows,
                conformance_passes=conformance.passes,
                mapped_columns=field_accounting.mapped_columns,
                preserved_native_only_columns=field_accounting.preserved_native_only_columns,
                unsupported_columns=field_accounting.unsupported_columns,
                lost_columns=field_accounting.lost_columns,
                source_sha256=provenance.source_sha256,
                config_sha256=provenance.config_sha256,
            )
        )

    total_accepted_rows = sum(entry.accepted_rows for entry in entries)
    total_rejected_rows = sum(entry.rejected_rows for entry in entries)
    passes = (
        not missing_artifacts
        and bool(entries)
        and all(entry.conformance_passes for entry in entries)
    )
    note = (
        "corpus coverage is complete and each normalization entry passed conformance checks"
        if passes
        else "corpus coverage is incomplete or has conformance failures requiring review"
    )
    return SearchEngineCorpusReport(
        adapter_kind=adapter_kind,
        corpus_root=str(corpus_root),
        entries=tuple(entries),
        missing_artifacts=tuple(sorted(set(missing_artifacts))),
        total_accepted_rows=total_accepted_rows,
        total_rejected_rows=total_rejected_rows,
        passes=passes,
        note=note,
    )


def build_comet_output_corpus_report(corpus_root: Path) -> SearchEngineCorpusReport:
    """Build corpus coverage over Comet native and pipeline-like outputs."""
    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.COMET,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.COMET,
                dialect_id="default",
                result_file="comet_results.tsv",
                config_file="comet.params",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.COMET,
                dialect_id="pipeline-export",
                result_file="comet_pipeline_export.tsv",
                config_file="comet.params",
            ),
        ),
    )


def build_msfragger_output_corpus_report(
    corpus_root: Path,
) -> SearchEngineCorpusReport:
    """Build corpus coverage over MSFragger native and pipeline-like outputs."""
    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MSFRAGGER,
                dialect_id="default",
                result_file="msfragger_results.tsv",
                config_file="msfragger.params",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MSFRAGGER,
                dialect_id="pipeline-export",
                result_file="msfragger_pipeline_export.tsv",
                config_file="msfragger.params",
            ),
        ),
    )


def build_sage_output_corpus_report(corpus_root: Path) -> SearchEngineCorpusReport:
    """Build corpus coverage over Sage native and pipeline-like outputs."""
    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.SAGE,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SAGE,
                dialect_id="default",
                result_file="sage_results.tsv",
                config_file="sage_search.json",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SAGE,
                dialect_id="pipeline-export",
                result_file="sage_pipeline_export.tsv",
                config_file="sage_search.json",
            ),
        ),
    )


def build_maxquant_output_corpus_report(
    corpus_root: Path,
) -> SearchEngineCorpusReport:
    """Build corpus coverage over MaxQuant evidence native and pipeline-like outputs."""
    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
                dialect_id="default",
                result_file="maxquant_evidence.tsv",
                config_file="maxquant_settings.txt",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
                dialect_id="pipeline-export",
                result_file="maxquant_pipeline_export.tsv",
                config_file="maxquant_settings.txt",
            ),
        ),
    )


def build_diann_output_corpus_report(corpus_root: Path) -> SearchEngineCorpusReport:
    """Build corpus coverage over DIA-NN report and pipeline-like exports."""
    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.DIANN,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.DIANN,
                dialect_id="default",
                result_file="diann_report.tsv",
                config_file="diann_config.json",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.DIANN,
                dialect_id="pipeline-export",
                result_file="diann_pipeline_export.tsv",
                config_file="diann_config.json",
            ),
        ),
    )


def build_spectronaut_output_corpus_report(
    corpus_root: Path,
) -> SearchEngineCorpusReport:
    """Build corpus coverage over Spectronaut-like native and pipeline exports."""
    return build_search_engine_corpus_report(
        corpus_root=corpus_root,
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
        input_specs=(
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SPECTRONAUT,
                dialect_id="default",
                result_file="spectronaut_report.tsv",
                config_file="spectronaut_settings.txt",
            ),
            SearchCorpusInputSpecification(
                adapter_kind=SearchAdapterKind.SPECTRONAUT,
                dialect_id="pipeline-export",
                result_file="spectronaut_pipeline_export.tsv",
                config_file="spectronaut_settings.txt",
            ),
        ),
    )


def _corpus_conformance_entry(
    report: SearchEngineCorpusReport,
) -> SearchAdapterCorpusConformanceEntry:
    unsupported_column_count = sum(
        len(entry.unsupported_columns) for entry in report.entries
    )
    lost_column_count = sum(len(entry.lost_columns) for entry in report.entries)
    return SearchAdapterCorpusConformanceEntry(
        adapter_kind=report.adapter_kind,
        corpus_root=report.corpus_root,
        corpus_passes=report.passes,
        corpus_entry_count=len(report.entries),
        total_accepted_rows=report.total_accepted_rows,
        total_rejected_rows=report.total_rejected_rows,
        unsupported_column_count=unsupported_column_count,
        lost_column_count=lost_column_count,
    )


def build_search_adapter_corpus_conformance_matrix(
    matrix_root: Path,
) -> SearchAdapterCorpusConformanceMatrix:
    """Build conformance summaries across built-in adapter corpora."""
    reports = (
        build_comet_output_corpus_report(matrix_root / "comet"),
        build_msfragger_output_corpus_report(matrix_root / "msfragger"),
        build_sage_output_corpus_report(matrix_root / "sage"),
        build_maxquant_output_corpus_report(matrix_root / "maxquant"),
        build_diann_output_corpus_report(matrix_root / "diann"),
        build_spectronaut_output_corpus_report(matrix_root / "spectronaut"),
    )
    entries = tuple(
        sorted(
            (_corpus_conformance_entry(report) for report in reports),
            key=lambda entry: entry.adapter_kind.value,
        )
    )
    return SearchAdapterCorpusConformanceMatrix(
        matrix_root=str(matrix_root),
        entries=entries,
        passes=all(entry.corpus_passes for entry in entries),
    )
