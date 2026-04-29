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
    SearchResultColumnMapping,
    SearchResultProvenanceManifest,
    SearchResultValidationIssue,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    build_calibration_plot_data,
    build_fdr_audit_trail,
    normalize_psm_records,
    normalize_psm_score_orientation,
    parse_psm_tsv,
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
    native_columns: tuple[str, ...] = Field(default_factory=tuple)


class SearchAdapterNormalizationReport(JsonModel):
    """Normalized records plus the adapter manifest that produced them."""

    model_config = ConfigDict(extra="forbid")

    adapter_manifest: SearchAdapterManifest
    family_policy: "SearchResultFamilyPolicy"
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    parse_report: PsmParseReport
    normalized_records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    evidence_rows: tuple["SearchNormalizedEvidenceEntry", ...] = Field(
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
    family_policy: "SearchResultFamilyPolicy"
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
            _MSFRAGGER_PIPELINE_DIALECT,
            _SAGE_PIPELINE_DIALECT,
            _MAXQUANT_PIPELINE_DIALECT,
            _DIANN_PIPELINE_DIALECT,
            _SPECTRONAUT_PIPELINE_DIALECT,
        ]
    )
    return {
        (dialect.adapter_kind, dialect.dialect_id): dialect for dialect in dialects
    }


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
            rows.append(
                {
                    str(key): str(value)
                    for key, value in row.items()
                    if key is not None
                }
            )
    return source_columns, tuple(rows)


def _mapped_column_names(mapping: SearchResultColumnMapping) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            column_name
            for column_name in (
                mapping.spectrum_id,
                mapping.peptide,
                mapping.charge,
                mapping.score,
                mapping.q_value,
                mapping.protein_refs,
                mapping.decoy_label,
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
        ("spectrum_id", mapping.spectrum_id),
        ("peptide", mapping.peptide),
        ("charge", mapping.charge),
        ("score", mapping.score),
        ("q_value", mapping.q_value),
        ("protein_refs", mapping.protein_refs),
        ("decoy_label", mapping.decoy_label),
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
    fixed_definitions = tuple(
        SearchModificationDefinition(
            site=str(site).upper(),
            mass_delta=float(mass_delta),
            variable=False,
            source_key=f"mods.static.{site}",
        )
        for site, mass_delta in sorted((mods_payload.get("static") or {}).items())
    )
    variable_definitions = tuple(
        SearchModificationDefinition(
            site=str(site).upper(),
            mass_delta=float(mass_delta),
            variable=True,
            source_key=f"mods.variable.{site}",
        )
        for site, deltas in sorted((mods_payload.get("variable") or {}).items())
        for mass_delta in deltas
    )
    precursor_unit = (
        SearchToleranceUnit.PPM
        if "ppm" in precursor_payload
        else SearchToleranceUnit.DA
        if "da" in precursor_payload
        else None
    )
    fragment_unit = (
        SearchToleranceUnit.PPM
        if "ppm" in fragment_payload
        else SearchToleranceUnit.DA
        if "da" in fragment_payload
        else None
    )
    database_path = database_payload.get("fasta")
    decoy_prefix = database_payload.get("decoy_tag")
    return SearchParameterReport(
        adapter_kind=SearchAdapterKind.SAGE,
        adapter_name="Sage",
        enzyme=str(enzyme_payload.get("name", "unknown")).strip().lower(),
        missed_cleavages=int(enzyme_payload["missed_cleavages"])
        if enzyme_payload.get("missed_cleavages") is not None
        else None,
        precursor_tolerance=float(
            precursor_payload.get("ppm", precursor_payload.get("da"))
        )
        if precursor_unit is not None
        else None,
        precursor_tolerance_unit=precursor_unit,
        fragment_tolerance=float(
            fragment_payload.get("ppm", fragment_payload.get("da"))
        )
        if fragment_unit is not None
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
    raise ValueError(
        f"search parameter parsing is not supported for adapter {adapter_kind.value!r}"
    )


def _supports_search_parameter_parsing(adapter_kind: SearchAdapterKind) -> bool:
    return adapter_kind in {
        SearchAdapterKind.COMET,
        SearchAdapterKind.MSFRAGGER,
        SearchAdapterKind.SAGE,
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
            [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in value
            ],
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
    resolved_mapping = mapping or (None if dialect is None else dialect.mapping) or manifest.mapping
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
